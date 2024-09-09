GC lifecycle management functionality. Filtering of GC Bundles for action implementation and queries
should be flexible for the end user and accommodate any combination of search parameters below for a specific Account:
<br>
- **Certificate Issuance ID** - Returns all GC Bundles with the specified Issuance ID. Implicitly limited to single Device and time period.\n
- **Bundle ID Range** - If Issuance ID is provided, returns a GC Bundle with certificate IDs inclusive of and between the integer GC Bundle ID range specified.\n
- **Issuance Time Period** - Returns all GC Bundles issued for generation that occured within the specified time period. If no Device is provided, result can include GC Bundles from multiple Devices.\n
- **Energy Source** - Returns all GC Bundles issued for generation derived from the specified energy source.\n
- **Production Device ID** - Returns all GC Bundles issued to the specified production Device.\n