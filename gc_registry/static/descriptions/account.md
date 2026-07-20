Accounts hold GC Bundles issued from zero or more Devices, and can transfer them
to other Accounts. Each Account can be managed by one or more Users with sufficient
access privileges.

Transfer permissions between Accounts are governed by a whitelist mechanism: each
Account maintains a list of Accounts that are permitted to send certificates to it.
Whitelist entries can be added or removed by Users with Trading User privileges or
above. Both the forward whitelist (who can send to me) and the inverse whitelist
(who I can send to) can be queried.

Account endpoints also provide access to associated Devices, Users, certificate
bundles, and a summary view aggregating key account metrics.
