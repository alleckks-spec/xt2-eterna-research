# Native file mode changes and profile loading

AI-assisted reverse engineering of X-T2 4.41 identified two bounded native counterexamples relevant to a custom-profile loader. These are offline ARM checks, not tests on a camera or mounted card.

In both mirrored filesystem modules, switching mode from 0 to 1 before calling the public close wrapper produces one successful callback while leaving supplied normal-mode handle state unchanged. The normal close worker and descriptor release are not reached. A successful callback alone therefore cannot establish reclamation of a normal-mode file after such a transition.

A received read request also consults the mode when its worker executes. A request prepared under mode 0 can enter the alternate backend after a mode change. The audit supplies the normal handle and received packet explicitly; the alternate backend is an error boundary, not a simulated successful media read.

The loader must coordinate normal file operations with mode changes. Keeping mode 0 from normal open submission through successful normal close completion is a conservative sufficient contract for these branches. This evidence does not prove that a particular global lock or lease implementation is necessary. An actual participating service owner or equivalent integration point remains unresolved; a mode snapshot alone does not provide exclusion.

Validation executed the original public close wrapper, mode setter/query and read worker for both modules. Assertions cover callback count, retained alias/descriptor/open-count/context state, worker mode-query visitation and absence of normal backend execution. The local report pins its source, two harness helpers and ten firmware units. No firmware binaries, vendor tables or raw disassembly are included here.

These findings keep the custom-profile loader's coordination requirement in place. They do not establish an integrated, ready-to-flash firmware or physical image fidelity.
