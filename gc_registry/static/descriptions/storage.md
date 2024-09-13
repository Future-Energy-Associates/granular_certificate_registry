The Storage Charge Record (SCR) is a record of the energy charged into a Storage Device from the grid or directly from another energy source.
All charging events must be recorded in an SCR following verification of metering reports from the storage unit.
Once recorded, an SCR can be allocated to a cancelled GC bundle issued in the same time period as the charging interval,
retaining the attributes of the GCs representing the energy charged. The Registry must ensure that a
process is in place to verify that the energy charged into the Storage Device is not double-counted or mismatched to the wrong
number of cancelled GC Bundles, and that the cancelled GC Bundles were issued within the charging interval indicated in the SCR.
<br>\n
A suggested approach to applying this requirement is to enforce a one-to-one relationship between SCRs and the cancelled GC Bundles,
allowing the full set of GC Bundle attributes to be referenced from the SCR and the subsequent SDR/SD-GC Bundle as a
single dependent chain without needing any aggregation or weighting algorithms. A disadvantage of this approach is that only a single
contiguous range of GC Bundle IDs can be allocated to each SCR, which in practice may lead to a large number of SCRs created due to
multiple non-contiguous GC Bundles being allocated in the same charging interval. More details can be found in the White Paper.
<br>\n
The Storage Discharge Record (SDR) is a record of the energy discharged by a Storage Device into the grid.
It is issued following the verification of a cancelled GC Bundle, a matching allocated SCR, and the proper allocation
of Storage Losses incurred during the charge interval. It is recommended that the methodology with which Storage Device
operators are permitted to allocate SDRs to SCRs, whether LIFO, FIFO, a weighted average, or operator's discretion, is
fixed such that operators cannot change the methodology in a way that would allow them to manipulate the allocation of SDRs.
<br>\n
To comply with the Standard, the Registry must provide a process to view the attributes of the underlying GC Bundles that
have been cancelled leading to the issuance of the SCR allocated to this SDR, by following the chain of one-to-one foreign
keys from the SDR to the SCR, and from the SCR to the cancelled GC Bundles.
<br>\n
The method for calulating the storage loss is not mandated, but the Registry must ensure that the method used is transparent and
clearly documented for auditing purposes. The method proposed in this API Specification followed the suggested methodology in the
EnergyTag Standard, which is to calculate the storage losses as the difference between the total input and output energy
of the Storage Device over a specified interval period (which shall not exceed 6 months for the initial efficiency factor
calculated from the start-up date of the Storage Device), implicitly including parasitic losses.