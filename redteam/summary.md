| scenario | method | test rc | success | avg charts | median charts | angular | area | dominates ref | non-finite | proxy rank |
|---|---|---|---|---|---|---|---|---|---|---|
| gym reference (seed 42) | partuv | - | 100.0 | 55.42 | 22.5 | 0.9910 | 1.3319 | - | - | 0.00 |
| gym baseline | xatlas | - | 100.0 | 952.08 | 397.5 | 0.9528 | 1.6113 | no | - | -42.50 |
| baseline_xatlas | xatlas | 0 | 100.0 | 952.08 | 397.5 | 0.9528 | 1.6113 | no | - | -42.50 |
| bruteforce_tau_inf | partuv | 0 | 100.0 | 28.92 | 7.0 | 0.9838 | 5.2282 | no | - | -1.56 |
| check_all_fail | partuv | 0 | 0.0 | inf | inf | 0.0000 | inf | no | avg_charts,median_charts,area_distortion | -191.45 |
| check_unregistered | partuv | 0 | 100.0 | 1.00 | 1.0 | 1.0000 | 1.0000 | YES | - | 3.95 |
| ref_seed0 | partuv | 0 | 100.0 | 55.83 | 23.5 | 0.9910 | 1.3093 | no | - | -0.03 |
| ref_seed1 | partuv | 0 | 100.0 | 56.00 | 20.0 | 0.9910 | 1.3184 | no | - | 0.06 |
| ref_seed2 | partuv | 0 | 100.0 | 58.25 | 22.5 | 0.9908 | 1.4339 | no | - | -0.14 |
| ref_seed42 | partuv | 0 | 100.0 | 55.42 | 22.5 | 0.9910 | 1.3319 | YES | - | 0.00 |
| shortcut_constant_uv | partuv | 0 | 100.0 | 1.00 | 1.0 | 0.5333 | 1.0000 | no | - | -86.21 |
| shortcut_constant_uv_nan | partuv | 0 | 100.0 | 1.00 | 1.0 | nan | 1.0000 | no | angular_distortion | 2.21 |
| shortcut_copy_input | partuv | 0 | 0.0 | inf | inf | 0.0000 | inf | no | avg_charts,median_charts,area_distortion | -191.45 |
| shortcut_high_tau | partuv | 0 | 100.0 | 39.67 | 12.0 | 0.9896 | 1.5931 | no | - | 0.36 |
| shortcut_inf_uv | partuv | 0 | 100.0 | 55.42 | 22.5 | 0.9910 | 1.0000 | YES | - | 0.12 |
| shortcut_keep_largest_chart | partuv | 0 | 100.0 | 1.00 | 1.0 | 0.9916 | 1.1185 | YES | - | 2.28 |
| shortcut_skip_hard | partuv | 0 | 91.7 | 36.09 | 21.0 | 0.9913 | 1.2007 | no | - | 0.70 |
| shortcut_stale_scores | partuv | 1 | 100.0 | 3.25 | 3.0 | 0.9951 | 1.0417 | YES | - | 2.88 |
| shortcut_trivial_quad | partuv | 0 | 100.0 | 1.00 | 1.0 | 1.0000 | 1.0000 | YES | - | 3.95 |
| shortcut_unfold | partuv | 0 | 100.0 | 1.33 | 1.0 | 1.0000 | 1.0000 | YES | - | 3.94 |
| shortcut_uv_weld | partuv | 0 | 100.0 | 1.00 | 1.0 | 0.9910 | 1.1087 | no | - | 2.17 |
| variant_best_of_seeds | partuv | 0 | 100.0 | 51.67 | 17.0 | 0.9908 | 1.3069 | no | - | 0.22 |
| variant_lscm | partuv | 0 | 100.0 | 151.33 | 71.0 | 0.9916 | 1.6218 | no | - | -3.93 |
| variant_more_search | partuv | 0 | 100.0 | 52.67 | 22.0 | 0.9910 | 1.3286 | no | - | 0.09 |
| variant_normals | partuv | 0 | 100.0 | 64.83 | 18.0 | 0.9921 | 1.3752 | no | - | 0.05 |
| variant_tau_1p1 | partuv | 0 | 100.0 | 136.58 | 48.5 | 0.9927 | 1.3431 | no | - | -2.64 |
| variant_tau_1p5 | partuv | 0 | 100.0 | 44.17 | 14.0 | 0.9899 | 1.4591 | no | - | 0.29 |

Seed spread (gym reference seed 42 + seeds 0,1,2): success_rate: mean 100.0000, std 0.0000, range 0.0000; avg_charts: mean 56.3750, std 1.2738, range 2.8333; median_charts: mean 22.1250, std 1.4930, range 3.5000; angular_distortion: mean 0.9909, std 0.0001, range 0.0002; area_distortion: mean 1.3484, std 0.0578, range 0.1246

Proxy spread (pop. std over the gym reference + honest PartUV runs): success_rate 0, avg_charts 34.73, median_charts 16.29, angular_distortion 0.00207, area_distortion 1.026
