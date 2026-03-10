import React, { useMemo } from "react";
import { Modal, Timeline, Typography, Tag, Button } from "antd";

const { Text } = Typography;

const normalizeDiffs = (diffs) => {
  if (Array.isArray(diffs)) return diffs;
  if (diffs && typeof diffs === "object") {
    return Object.entries(diffs).map(([field, v]) => ({
      field,
      before: v?.before,
      after: v?.after,
    }));
  }
  return [];
};

const statusColor = (status) => {
  switch (status) {
    case "Cancelled":
      return "red";
    case "Cancelled for Storage":
      return "orange";
    case "Claimed":
      return "green";
    case "Reserved":
      return "gold";
    case "Locked":
      return "gray";
    case "Withdrawn":
      return "gray";
    case "Bundle Split":
      return "purple";
    case "Active":
      return "green";
    default:
      return "blue";
  }
};

const classify = (e) => {
  const diffs = normalizeDiffs(e.diffs);
  const diffMap = Object.fromEntries(
    diffs.map((d) => [d.field, { before: d.before, after: d.after }])
  );

  if (e.event_type === "CREATE") {
    if (e.parent_entity_id != null) {
      if (e.kind === "time_shifted") {
        return {
          label: `Time-shifted: #${e.entity_id} from #${e.parent_entity_id}`,
          color: "blue",
        };
      } else {
        return {
          label: `Split: child #${e.entity_id} from #${e.parent_entity_id}`,
          color: "purple",
        };
      }
    }
    return { label: `Bundle created #${e.entity_id}`, color: "green" };
  }
  if (e.event_type === "DELETE") {
    return { label: `Bundle #${e.entity_id} deleted`, color: "red" };
  }
  if (e.event_type === "UPDATE") {
    if (diffMap.account_id) {
      const { before, after } = diffMap.account_id;
      return {
        label: `Transferred: account ${before} → ${after}`,
        color: "blue",
      };
    }
    if (diffMap.certificate_bundle_status) {
      const { after } = diffMap.certificate_bundle_status;
      return { label: `Status: ${after}`, color: statusColor(after) };
    }
    return { label: "Bundle updated", color: "gray" };
  }
  return { label: e.event_type, color: "gray" };
};

const CertificateLineageDialog = ({ open, onClose, lineage }) => {
  const events = useMemo(() => {
    if (!lineage?.timeline) return [];
    const sorted = [...lineage.timeline].sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    );
    return sorted.map((e) => {
      const meta = classify(e);
      return {
        key: `${e.event_type}:${e.entity_id}:${e.timestamp}`,
        color: meta.color,
        children: (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <Text strong>{meta.label}</Text>
              <Text type="secondary">
                {new Date(e.timestamp).toLocaleString()}
              </Text>
            </div>
            <div style={{ marginTop: 4 }}>
              {normalizeDiffs(e.diffs).map((d) => (
                <div key={d.field} style={{ fontSize: 12 }}>
                  <Text type="secondary">{d.field}: </Text>
                  <Tag color="default">{String(d.before)}</Tag>
                  <span style={{ margin: "0 4px" }}>→</span>
                  <Tag color="processing">{String(d.after)}</Tag>
                </div>
              ))}
            </div>
          </div>
        ),
      };
    });
  }, [lineage]);

  if (!lineage) return null;

  // Support both raw lineage and formatted timeline payloads
  const bundleId = lineage.bundle_id ?? lineage.bundle?.bundle_id;
  const issuanceId = lineage.issuance_id ?? lineage.bundle?.issuance_id;

  const buildLineageExport = (lineageObj) => {
    const sorted = [...(lineageObj?.timeline || [])].sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    );
    const eventsExport = sorted.map((e, idx) => ({
      index: idx,
      timestamp: e.timestamp,
      event_type: e.event_type,
      entity_id: e.entity_id,
      parent_entity_id: e.parent_entity_id ?? null,
      label: classify(e).label,
      kind: classify(e).kind || "update",
      diffs: Array.isArray(e.diffs) ? e.diffs : normalizeDiffs(e.diffs),
      attributes_before: e.attributes_before || {},
      attributes_after: e.attributes_after || {},
    }));
    return {
      version: "1.0.0",
      exported_at: new Date().toISOString(),
      bundle: {
        bundle_id: bundleId,
        issuance_id: issuanceId,
        lineage_path: lineageObj.lineage_path || [],
        created_at: lineageObj.created_at || null,
        last_updated_at: lineageObj.last_updated_at || null,
        current_state: lineageObj.current_state || {},
      },
      events: eventsExport,
      graph: {
        nodes: Array.from(
          new Set(eventsExport.flatMap((e) => [e.entity_id, e.parent_entity_id].filter(Boolean)))
        ).map((id) => ({ id })),
        edges: eventsExport
          .filter((e) => e.parent_entity_id != null)
            .map((e) => ({
            from: e.parent_entity_id,
            to: e.entity_id,
            type: e.kind === "time_shifted" ? "time_shift" : "split",
          })),
      },
    };
  };

  const downloadJSON = (obj, filename) => {
    const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Modal
      title="Certificate Lineage"
      open={open}
      onCancel={onClose}
      width={720}
      footer={null}
    >
      <div style={{ padding: 16 }}>
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ marginRight: 16 }}>
            Bundle ID:
          </Text>
          <Text strong>{bundleId}</Text>
        </div>
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ marginRight: 16 }}>
            Issuance ID:
          </Text>
        <Text strong>{issuanceId}</Text>
        </div>
        <Timeline items={events} />
      </div>
      <div style={{ padding: 16 }}>
        <Button
          type="primary"
          onClick={() =>
            downloadJSON(
              buildLineageExport(lineage),
              `lineage_${issuanceId || bundleId || "bundle"}.json`
            )
          }
        >
          Download Lineage
        </Button>
      </div>
    </Modal>
  );
};

export default CertificateLineageDialog;