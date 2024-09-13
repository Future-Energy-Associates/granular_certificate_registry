This document outlines the EnergyTag API Specification to accompany Version 2 of
the EnergyTag Standard.
The functionality outlined within each API interaction represents the recommended
minimum required detail necessary to implement a consistent Granular Certificate
(GC) registry system.
Within the Certificates section, the definition of GCs as specified in the Create
Certificate POST request, alongside the filtering parameters required to instigate
query, transfer, and cancellation requests, will form core components of the standard
and impact the functionality of the registry the greatest. Subsequent sections
describing Organisation, User, Account, and Device management are **recommendations
only** and do not form part of the standard, although terminology used therein is
referenced in the certificate definitions. They are included in the database class
diagram for the sake of completeness in representing the relationships between the
certificate and action definitions; the fields implemented for these tables are
left to the discretion of the registry operator.
<br>\n
Where Universally Unique Identifiers (UUIDs) have been used, these can be replaced with
any consistent and unique identification mechanism preferred by the registry; for
example, concatenations of datetime and Device ID). It is recommended that GC Bundle
IDs remain represented as integers, or an initial string concatenated with an integer,
that can be both uniquely referenced and unambiguously incremented to simplify the
GC Bundle subdivision process.
<br>\n
Each API call defined below is to be interpreted as an instance of an object that is
stored by the registry upon receipt by a User, and can be updated as it moves from
received, through pending, to resolved within a transaction log uniquely identified
by an action ID. With this in mind, fields such as `action_completed_datetime` are
not to be interpreted as attributes supplied by the User, but fields that are
populated and updated by the registry as the request is processed.
This approach allows any and all actions to be queried and traced, with relevant
User access rights left to the discretion of the registry operator.
<br>\n
[Click here](https://pasteboard.co/KHFQcxYCoRPL.png) to view the GC model class diagram
for this specification, [here](https://pasteboard.co/KHFQcxYCoRPL.png) for the Storage class diagram and
[click here](https://pasteboard.co/KIRLh9VKr2KO.png) to
view a graphical example of a GC Bundle issuance, transfer, and cancellation that
illustrates the principles of the GC Bundle subdivision and management processes.
