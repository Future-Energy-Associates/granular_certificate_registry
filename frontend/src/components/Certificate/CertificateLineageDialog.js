import React, { useMemo } from "react";
import { Modal, Timeline, Typography, Tag } from "antd";

const { Text } = Typography;

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

const normalizeDiffs = (diffs) => {
    if (Array.isArray(diffs)) return diffs;
    if (diffs && typeof diffs == "object") {
        return Object.entries(diffs).map(([field, v]) => ({
            field,
            before: v?.before,
            after: v?.after,
        }));
    }
    return [];
};

const classify = (e) => {
  const diffs = normalizeDiffs(e.diffs);
  const diffMap = Object.fromEntries(
    diffs.map((d) => [d.field, { before: d.before, after: d.after }])
  );

  if (e.event_type === "CREATE") {
    if (e.parent_entity_id != null) {
      return {
        label: `Split: child #${e.entity_id} from #${e.parent_entity_id}`,
        color: "purple",
      };
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
          <Text strong>{lineage.bundle_id}</Text>
        </div>
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ marginRight: 16 }}>
            Issuance ID:
          </Text>
          <Text strong>{lineage.issuance_id}</Text>
        </div>
        <Timeline items={events} />
      </div>
    </Modal>
  );
};

export default CertificateLineageDialog;