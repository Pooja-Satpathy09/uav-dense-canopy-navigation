"""Explicit height-tracking loss for DiffPhysDrone (apply after add_height_aware.py; safe to re-run).

New option for main_cuda.py:
  --coef_height C   adds C * L_height, where L_height is the smooth-L1 error between the drone's height
                    and the target height, weighted by a ramp 0 -> 1 over the episode (early deviations
                    are cheap, so the drone may still dodge obstacles vertically, but it must reach the
                    target height as the flight goes on). Default 0 = unchanged training.
"""
from pathlib import Path

EDITS = [
    ("parser.add_argument('--target_dz', type=float, default=0.0,\n",
     "parser.add_argument('--coef_height', type=float, default=0.0,\n"
     "                    help='weight of the ramped height-tracking loss (0 = off)')\n"
     "parser.add_argument('--target_dz', type=float, default=0.0,\n"),
    ("    loss_ground_affinity = p_history[..., 2].relu().pow(2).mean()\n",
     "    loss_ground_affinity = p_history[..., 2].relu().pow(2).mean()\n"
     "    height_ramp = torch.linspace(0, 1, p_history.shape[0], device=p_history.device)[:, None]\n"
     "    loss_height = (height_ramp * F.smooth_l1_loss(\n"
     "        p_history[..., 2], env.p_target[None, :, 2].expand_as(p_history[..., 2]), reduction='none')).mean()\n"),
    ("         else args.coef_ground_affinity + loss_ground_affinity)\n",
     "         else args.coef_ground_affinity + loss_ground_affinity) + \\\n"
     "        args.coef_height * loss_height\n"),
    ("            'loss_ground_affinity': loss_ground_affinity,\n",
     "            'loss_ground_affinity': loss_ground_affinity,\n"
     "            'loss_height': loss_height,\n"),
]
f = Path("main_cuda.py")
text = f.read_text()
if "--coef_height" in text:
    print("main_cuda.py: height loss already added, skipped")
else:
    for old, new in EDITS:
        if text.count(old) != 1:
            raise SystemExit(f"expected one match for {old!r}, found {text.count(old)}; nothing written")
        text = text.replace(old, new)
    f.write_text(text)
    print(f"main_cuda.py: height loss added ({len(EDITS)} edits)")
