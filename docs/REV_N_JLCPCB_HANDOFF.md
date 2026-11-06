# Rev N JLCPCB handoff boundary

The supplied fabrication README marks the Seeed XIAO Sense as **not assembled / hand-soldered**. The existing BOM/CPL therefore does not authorize an automatic assumption that JLCPCB will source, install, program or functionally test the module.

JLCPCB's official documentation describes consigned-parts handling and personalized services including programming when the customer supplies the chip/interface information, board photos and BIN/HEX. Those services require review/quotation; consigned parts are not functionally tested by default. Obtain written engineering acceptance for the exact XIAO module, manual solder process, firmware image/address, fixture and test specification before assigning those operations to JLCPCB.

Sources: [JLCPCB consignment terms](https://jlcpcb.com/help/article/consignment-part-terms-conditions), [parts sourcing instructions](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction), [supported personalized services](https://jlcpcb.com/help/article/jlcpcb-supported-personalized-services).

## Default division of responsibility

| Stage | Default owner without a special written agreement |
|---|---|
| PCB manufacture, BOM/CPL SMT assembly, normal AOI/process checks | JLCPCB order |
| XIAO Sense procurement/installation | Post-assembly integrator |
| Camera/microSD/module connection | Post-assembly integrator |
| Firmware flashing and hash recording | Post-assembly integrator |
| Functional camera/mic/speaker/button/INA/NTC/LED/light tests | Post-assembly integrator |
| NCHG tap installation and charger-state validation | Qualified integrator after electrical approval |

Do not send the design to production as “fully tested PCBA” merely because the bare carrier passes JLC process checks. The functional path depends on the post-installed XIAO Sense and peripherals.

