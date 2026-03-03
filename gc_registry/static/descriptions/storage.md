The Storage Record captures energy charged into or discharged from a Storage Device as
verified from metering reports. Each record specifies the Device, the flow direction
(charge or discharge), the time interval, and the energy quantity in Watt-hours.
Storage Records are submitted as a CSV file via the registry, and the registry validates
the data against the specified Storage Device before persisting the records.

Once charge and discharge records have been submitted and validated, they can be
paired into Allocated Storage Records by a Storage Validator. An Allocated Storage
Record links a Storage Charge Record (SCR) to a Storage Discharge Record (SDR) at a
specified proportion, along with the allocation methodology (e.g. FIFO, LIFO, weighted
average, or operator's discretion), the efficiency factor, and the methodology used to
calculate storage losses. It is recommended that the allocation methodology is fixed
such that operators cannot change it in a way that would allow manipulation of the
allocation. Each Allocated Storage Record may also reference the cancelled GC Bundle
that corresponds to the energy charged, and the SD-GC Bundle issued against the
discharged energy.

A Storage Discharge GC (SD-GC) Bundle is issued following the verification of a
cancelled GC Bundle, a matching Allocated Storage Record, and the proper application
of storage losses. The SD-GC Bundle is issued to the Account of the Storage Device
and retains the attributes of the underlying cancelled GC Bundles. These bundles
can be queried using the same GC Bundle query endpoints as regular GC Bundles, with
the additional option to filter by storage ID and discharging start datetime.

To comply with the Standard, the Registry must provide a process to view the attributes
of the underlying GC Bundles that have been cancelled leading to the issuance of the
Allocated Storage Record, by following the chain of foreign keys from the SD-GC
through the Allocated Storage Record to the original cancelled GC Bundles.

The method for calculating storage losses is not mandated, but the Registry must
ensure that the method used is transparent and clearly documented for auditing purposes.
The method proposed in this API Specification follows the suggested methodology in the
EnergyTag Standard, which is to calculate the storage losses as the difference between
the total input and output energy of the Storage Device over a specified interval period
(which shall not exceed 6 months for the initial efficiency factor calculated from the
start-up date of the Storage Device), implicitly including parasitic losses.
