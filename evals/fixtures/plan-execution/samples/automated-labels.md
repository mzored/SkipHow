# Representative uniform log labels

Old record: `shipment_rejected supplier={supplier} row={row}`.
Accepted record: `shipment_declined supplier={supplier} row={row}`.
The established codemod changes only the event label in the structured log catalogue.
It leaves the parameter sequence and message payload unchanged for every entry.
No supplier-specific rule or authored explanation is part of this transformation.
