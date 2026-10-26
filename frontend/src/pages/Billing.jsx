import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Billing() {
  const [invoices, setInvoices] = useState([]);
  const [message, setMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [paymentMethods, setPaymentMethods] = useState({});
  const [loadingInvoice, setLoadingInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState("");

  const [invoiceForm, setInvoiceForm] = useState({
    reservation_id: "",
    discount: "0",
    tax_percentage: "10",
  });

  // Extract user role from JWT token
  const token = localStorage.getItem("token");
  let role = "";
  try {
    if (token) {
      const payload = JSON.parse(
        atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
      );
      role = payload.role || "";
    }
  } catch {
    role = "";
  }

  const canManageBilling = ["ADMIN", "FINANCE", "RECEPTIONIST", "MANAGER"].includes(role);

  const loadInvoices = useCallback(async () => {
    setLoading(true);

    try {
      const response = await api.get("/invoices/");
      setInvoices(response.data);
      setMessage("");
    } catch (error) {
      console.error("loadInvoices error:", error);
      let detail = "Unable to load invoices.";
      if (typeof error.response?.data?.detail === "string") {
        detail = error.response.data.detail;
      } else if (error.response?.status === 403) {
        detail = "Access denied: Your account role does not have permission to view billing.";
      } else if (error.response?.status) {
        detail = `Backend server returned status ${error.response.status}. Please check backend logs.`;
      } else if (error.message) {
        detail = `${error.message}. Is the backend server running?`;
      }
      setMessage(detail);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadInvoices();
    }, 0);

    return () => clearTimeout(timer);
  }, [loadInvoices]);

  const handleGenerateInvoice = async (e) => {
    e.preventDefault();
    setGenerateError("");
    setSuccessMessage("");

    if (!invoiceForm.reservation_id) {
      setGenerateError("Reservation ID is required.");
      return;
    }

    setGenerating(true);
    try {
      await api.post("/invoices/", {
        reservation_id: Number(invoiceForm.reservation_id),
        discount: Number(invoiceForm.discount || 0),
        tax_percentage: Number(invoiceForm.tax_percentage || 10),
      });

      setSuccessMessage(`Invoice for Reservation #${invoiceForm.reservation_id} generated successfully!`);
      setShowGenerateModal(false);
      setInvoiceForm({ reservation_id: "", discount: "0", tax_percentage: "10" });
      await loadInvoices();
    } catch (err) {
      console.error(err);
      let errDetail = "Failed to generate invoice.";
      if (typeof err.response?.data?.detail === "string") {
        errDetail = err.response.data.detail;
      } else if (Array.isArray(err.response?.data?.detail)) {
        errDetail = err.response.data.detail.map((d) => d.msg).join("; ");
      } else if (err.message) {
        errDetail = err.message;
      }
      setGenerateError(errDetail);
    } finally {
      setGenerating(false);
    }
  };

  const handlePayment = async (invoice) => {
    const method = paymentMethods[invoice.id] || "UPI";

    if (Number(invoice.total) <= 0) {
      setMessage(
        `Invoice #${invoice.id} has no payable amount. Check its charges first.`
      );
      return;
    }

    const confirmed = window.confirm(
      `Record a simulated payment of ₹${Number(invoice.total).toFixed(2)} for Invoice #${invoice.id}?`
    );

    if (!confirmed) return;

    setLoadingInvoice(invoice.id);
    setMessage("");

    try {
      await api.post("/payments/", {
        invoice_id: invoice.id,
        amount: Number(invoice.total),
        payment_method: method,
      });

      setSuccessMessage(`Payment of ₹${Number(invoice.total).toFixed(2)} recorded for Invoice #${invoice.id}.`);
      await loadInvoices();
    } catch (error) {
      console.error(error);
      setMessage(
        error.response?.data?.detail || "Failed to record payment."
      );
    } finally {
      setLoadingInvoice(null);
    }
  };

  const totalInvoices = invoices.length;

  const paidInvoices = invoices.filter(
    (invoice) => invoice.status === "PAID"
  );

  const unpaidInvoices = invoices.filter(
    (invoice) => invoice.status !== "PAID"
  );

  const outstandingAmount = unpaidInvoices.reduce(
    (sum, invoice) => sum + Number(invoice.total || 0),
    0
  );

  const totalPaid = paidInvoices.reduce(
    (sum, invoice) => sum + Number(invoice.total || 0),
    0
  );

  const formatMoney = (amount) =>
    Number(amount || 0).toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    });

  const cardStyle = {
    background: "#ffffff",
    border: "1px solid #e5eaf1",
    borderRadius: "12px",
    padding: "22px",
    boxShadow: "0 3px 12px rgba(15, 23, 42, 0.035)",
  };

  const buttonStyle = {
    background: "#0f766e",
    color: "#ffffff",
    border: "none",
    padding: "10px 18px",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "14px",
  };

  const linkStyle = {
    background: "#ffffff",
    color: "#0f766e",
    border: "1px solid #0f766e",
    padding: "10px 18px",
    borderRadius: "8px",
    textDecoration: "none",
    fontSize: "14px",
    display: "inline-flex",
    alignItems: "center",
  };

  const statusStyle = (status) => {
    if (status === "PAID") {
      return { background: "#d1fae5", color: "#065f46" };
    }
    if (status === "PARTIALLY_PAID") {
      return { background: "#fef3c7", color: "#92400e" };
    }
    return { background: "#fee2e2", color: "#991b1b" };
  };

  const tableCellStyle = {
    padding: "14px 12px",
    borderBottom: "1px solid #e5eaf1",
    fontSize: "14px",
    textAlign: "left",
  };

  const labelStyle = {
    display: "block",
    fontSize: "13px",
    fontWeight: 600,
    color: "#334155",
    marginBottom: "6px",
  };

  const inputStyle = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "8px",
    border: "1px solid #cbd5e1",
    fontSize: "14px",
    boxSizing: "border-box",
    background: "#ffffff",
    color: "#1e293b",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f4f7fb",
        padding: "32px",
        color: "#17243a",
        boxSizing: "border-box",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "16px",
          flexWrap: "wrap",
          marginBottom: "28px",
        }}
      >
        <div>
          <h1
            style={{
              margin: "0 0 8px",
              fontSize: "30px",
              lineHeight: "1.3",
              fontWeight: 700,
              color: "#17243a",
            }}
          >
            Billing &amp; Invoices
          </h1>

          <p style={{ margin: 0, color: "#64748b", fontSize: "14px" }}>
            Generate invoices, review guest folios, and record payments.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          {canManageBilling && (
            <button
              type="button"
              onClick={() => {
                setShowGenerateModal(true);
                setGenerateError("");
              }}
              style={{
                ...buttonStyle,
                background: "#0f766e",
              }}
            >
              + Generate Invoice
            </button>
          )}

          <button
            type="button"
            onClick={loadInvoices}
            disabled={loading}
            style={buttonStyle}
          >
            {loading ? "Loading..." : "Refresh Invoices"}
          </button>

          <Link to="/dashboard" style={linkStyle}>
            Dashboard
          </Link>
        </div>
      </div>

      {successMessage && (
        <div
          style={{
            background: "#dcfce7",
            color: "#166534",
            padding: "12px 18px",
            borderRadius: "8px",
            marginBottom: "20px",
            border: "1px solid #bbf7d0",
            fontWeight: 500,
          }}
        >
          {successMessage}
        </div>
      )}

      {message && (
        <div
          role="status"
          style={{
            background: "#fee2e2",
            border: "1px solid #fecaca",
            color: "#991b1b",
            padding: "13px 16px",
            borderRadius: "8px",
            marginBottom: "22px",
            fontSize: "14px",
          }}
        >
          {message}
        </div>
      )}

      {/* Generate Invoice Modal */}
      {showGenerateModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background: "rgba(15, 23, 42, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
            boxSizing: "border-box",
          }}
        >
          <div
            style={{
              background: "#ffffff",
              borderRadius: "14px",
              padding: "28px",
              width: "100%",
              maxWidth: "480px",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "20px",
              }}
            >
              <h2 style={{ margin: 0, fontSize: "20px", color: "#17243a" }}>
                Generate New Invoice
              </h2>
              <button
                type="button"
                onClick={() => setShowGenerateModal(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  fontSize: "20px",
                  cursor: "pointer",
                  color: "#64748b",
                }}
              >
                ✕
              </button>
            </div>

            {generateError && (
              <p
                style={{
                  color: "#b91c1c",
                  background: "#fee2e2",
                  padding: "10px",
                  borderRadius: "6px",
                  fontSize: "14px",
                  marginBottom: "16px",
                }}
              >
                {generateError}
              </p>
            )}

            <form onSubmit={handleGenerateInvoice}>
              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Reservation ID *</label>
                <input
                  type="number"
                  value={invoiceForm.reservation_id}
                  onChange={(e) => setInvoiceForm({ ...invoiceForm, reservation_id: e.target.value })}
                  placeholder="e.g. 1"
                  min="1"
                  style={inputStyle}
                  required
                />
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "14px",
                  marginBottom: "24px",
                }}
              >
                <div>
                  <label style={labelStyle}>Discount (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={invoiceForm.discount}
                    onChange={(e) => setInvoiceForm({ ...invoiceForm, discount: e.target.value })}
                    placeholder="0"
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={labelStyle}>Tax Percentage (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={invoiceForm.tax_percentage}
                    onChange={(e) => setInvoiceForm({ ...invoiceForm, tax_percentage: e.target.value })}
                    placeholder="10"
                    style={inputStyle}
                  />
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  style={{
                    ...buttonStyle,
                    background: "#f1f5f9",
                    color: "#475569",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating}
                  style={{
                    ...buttonStyle,
                    background: "#0f766e",
                  }}
                >
                  {generating ? "Generating..." : "Generate Folio"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Summary cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "18px",
          marginBottom: "28px",
        }}
      >
        <div style={cardStyle}>
          <p style={{ color: "#64748b", fontSize: "13px", margin: "0 0 12px" }}>
            TOTAL INVOICES
          </p>
          <h2 style={{ margin: 0, fontSize: "28px" }}>{totalInvoices}</h2>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#64748b", fontSize: "13px", margin: "0 0 12px" }}>
            PAID INVOICES
          </p>
          <h2 style={{ margin: 0, fontSize: "28px", color: "#0f766e" }}>
            {paidInvoices.length}
          </h2>
          <p style={{ color: "#64748b", fontSize: "13px", margin: "8px 0 0" }}>
            {formatMoney(totalPaid)} in paid invoice totals
          </p>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#64748b", fontSize: "13px", margin: "0 0 12px" }}>
            UNPAID INVOICES
          </p>
          <h2 style={{ margin: 0, fontSize: "28px", color: "#b91c1c" }}>
            {unpaidInvoices.length}
          </h2>
          <p style={{ color: "#64748b", fontSize: "13px", margin: "8px 0 0" }}>
            {formatMoney(outstandingAmount)} in unpaid invoice totals
          </p>
        </div>
      </div>

      {/* Invoice table */}
      <section style={cardStyle}>
        <h2 style={{ margin: "0 0 20px", fontSize: "21px" }}>
          All Invoices
        </h2>

        {loading ? (
          <p>Loading invoices...</p>
        ) : invoices.length === 0 ? (
          <p>No invoices found.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  {[
                    "Invoice",
                    "Reservation",
                    "Subtotal",
                    "Discount",
                    "Tax",
                    "Total",
                    "Status",
                    "Payment",
                  ].map((heading) => (
                    <th key={heading} style={tableCellStyle}>
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td style={tableCellStyle}>
                      <strong>#{invoice.id}</strong>
                    </td>
                    <td style={tableCellStyle}>#{invoice.reservation_id}</td>
                    <td style={tableCellStyle}>{formatMoney(invoice.subtotal)}</td>
                    <td style={tableCellStyle}>{formatMoney(invoice.discount)}</td>
                    <td style={tableCellStyle}>{formatMoney(invoice.tax)}</td>
                    <td style={tableCellStyle}>
                      <strong>{formatMoney(invoice.total)}</strong>
                    </td>
                    <td style={tableCellStyle}>
                      <span
                        style={{
                          ...statusStyle(invoice.status),
                          padding: "5px 10px",
                          borderRadius: "20px",
                          fontSize: "12px",
                          fontWeight: 600,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {invoice.status}
                      </span>
                    </td>
                    <td style={tableCellStyle}>
                      {invoice.status === "PAID" ? (
                        <span style={{ color: "#065f46", fontWeight: 600 }}>
                          Settled
                        </span>
                      ) : (
                        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                          <select
                            value={paymentMethods[invoice.id] || "UPI"}
                            onChange={(e) =>
                              setPaymentMethods({
                                ...paymentMethods,
                                [invoice.id]: e.target.value,
                              })
                            }
                            style={{
                              padding: "6px 10px",
                              borderRadius: "6px",
                              border: "1px solid #cbd5e1",
                              fontSize: "13px",
                            }}
                          >
                            <option value="UPI">UPI</option>
                            <option value="CASH">Cash</option>
                            <option value="CREDIT_CARD">Credit Card</option>
                            <option value="DEBIT_CARD">Debit Card</option>
                            <option value="BANK_TRANSFER">Bank Transfer</option>
                          </select>

                          <button
                            type="button"
                            onClick={() => handlePayment(invoice)}
                            disabled={loadingInvoice === invoice.id}
                            style={{
                              ...buttonStyle,
                              padding: "6px 14px",
                              fontSize: "13px",
                            }}
                          >
                            {loadingInvoice === invoice.id ? "Processing..." : "Pay"}
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default Billing;
