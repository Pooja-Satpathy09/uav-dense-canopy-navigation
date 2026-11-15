"""Height-aware training for DiffPhysDrone (run inside simulator/DiffPhysDrone).

New options for main_cuda.py (both off by default, so training is unchanged without them):
  --ground_affinity_fix  multiply the ground-affinity loss by --coef_ground_affinity instead of
                         adding the two (upstream line 213 adds them, so the 'legacy, off' term is
                         always on with weight 1 and pulls the drone below z = 0)
  --target_dz D          offset each training target height by U(-D, D) m, clamped to [-0.6, 1.5]
                         (upstream samples start and target at the same height)
Run once:  python add_height_aware.py   (safe to re-run)
"""
from pathlib import Path

EDITS = {
    "main_cuda.py": [
        ("parser.add_argument('--cam_angle', type=int, default=10)\n",
         "parser.add_argument('--cam_angle', type=int, default=10)\n"
         "parser.add_argument('--ground_affinity_fix', action='store_true',\n"
         "                    help='multiply (not add) coef_ground_affinity and the ground-affinity loss')\n"
         "parser.add_argument('--target_dz', type=float, default=0.0,\n"
         "                    help='random target height offset U(-dz, dz) in metres (0 = upstream)')\n"),
        ("env = Env(args.batch_size, 64, 48, args.grad_decay, device,",
         "env = Env(args.batch_size, 64, 48, args.grad_decay, device, target_dz=args.target_dz,"),
        ("        args.coef_ground_affinity + loss_ground_affinity",
         "        (args.coef_ground_affinity * loss_ground_affinity if args.ground_affinity_fix\n"
         "         else args.coef_ground_affinity + loss_ground_affinity)"),
    ],
    "env_cuda.py": [
        ("random_rotation=False, cam_angle=10) -> None:",
         "random_rotation=False, cam_angle=10, target_dz=0.0) -> None:"),
        ("        self.single = single\n",
         "        self.single = single\n        self.target_dz = target_dz\n"),
        ("        self.p_target = self.p_end * scale + torch.randn_like(scale) * 0.1\n",
         "        self.p_target = self.p_end * scale + torch.randn_like(scale) * 0.1\n"
         "        if self.target_dz > 0:\n"
         "            dz = (torch.rand((B, 1), device=device) * 2 - 1) * self.target_dz\n"
         "            self.p_target = torch.cat([self.p_target[:, :2],\n"
         "                                       (self.p_target[:, 2:] + dz).clamp(-0.6, 1.5)], -1)\n"),
    ],
}
MARKERS = {"main_cuda.py": "--ground_affinity_fix", "env_cuda.py": "self.target_dz"}
for path, edits in EDITS.items():
    f = Path(path)
    text = f.read_text()
    if MARKERS[path] in text:
        print(f"{path}: already patched, skipped")
        continue
    for old, new in edits:
        if text.count(old) != 1:
            raise SystemExit(f"{path}: expected one match for {old!r}, found {text.count(old)}; nothing written")
        text = text.replace(old, new)
    f.write_text(text)
    print(f"{path}: patched ({len(edits)} edits)")
