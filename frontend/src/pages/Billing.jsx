import { useCallback, useEffect, useState } from "react";
import api from "../services/api";

function Billing() {
  const [invoices, setInvoices] = useState([]);
  const [message, setMessage] = useState("");
  const [paymentMethods, setPaymentMethods] = useState({});
  const [loadingInvoice, setLoadingInvoice] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadInvoices = useCallback(async () => {
    setLoading(true);

    try {
      const response = await api.get("/invoices/");
      setInvoices(response.data);
      setMessage("");
    } catch (error) {
      console.error(error);
      setMessage("Unable to load invoices.");
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

      setMessage(`Payment recorded for Invoice #${invoice.id}.`);
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
    padding: "10px 15px",
    borderRadius: "7px",
    cursor: "pointer",
    fontWeight: 600,
  };

  const statusStyle = (status) => {
    if (status === "PAID") {
      return { background: "#d1fae5", color: "#065f46" };
    }

    return { background: "#fef3c7", color: "#92400e" };
  };

  const tableCellStyle = {
    padding: "14px 12px",
    borderBottom: "1px solid #e5eaf1",
    fontSize: "13px",
    textAlign: "left",
    whiteSpace: "nowrap",
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
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "15px",
          flexWrap: "wrap",
          marginBottom: "28px",
        }}
      >
        <div>
          <h1
            style={{
              margin: "0 0 8px",
              fontSize: "30px",
              lineHeight: 1.3,
            }}
          >
            Billing &amp; Invoices
          </h1>

          <p style={{ margin: 0, color: "#64748b", fontSize: "14px" }}>
            Manage invoice balances and record simulated payments.
          </p>
        </div>

        <button
          type="button"
          onClick={loadInvoices}
          disabled={loading}
          style={buttonStyle}
        >
          {loading ? "Loading..." : "Refresh Invoices"}
        </button>
      </div>

      {message && (
        <div
          role="status"
          style={{
            background: "#ffffff",
            border: "1px solid #dbe5ef",
            padding: "13px 16px",
            borderRadius: "8px",
            marginBottom: "22px",
          }}
        >
          {message}
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
          <p style={{ color: "#64748b", fontSize: "13px" }}>
            {formatMoney(totalPaid)} in paid invoice totals
          </p>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#64748b", fontSize: "13px", margin: "0 0 12px" }}>
            UNPAID INVOICES
          </p>
          <h2 style={{ margin: 0, fontSize: "28px", color: "#b45309" }}>
            {unpaidInvoices.length}
          </h2>
          <p style={{ color: "#64748b", fontSize: "13px" }}>
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
                          padding: "6px 10px",
                          borderRadius: "20px",
                          fontSize: "11px",
                          fontWeight: 700,
                        }}
                      >
                        {invoice.status}
                      </span>
                    </td>
                    <td style={tableCellStyle}>
                      {invoice.status !== "PAID" && Number(invoice.total) > 0 ? (
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                          }}
                        >
                          <select
                            aria-label={`Payment method for invoice ${invoice.id}`}
                            value={paymentMethods[invoice.id] || "UPI"}
                            disabled={loadingInvoice === invoice.id}
                            onChange={(event) =>
                              setPaymentMethods((previous) => ({
                                ...previous,
                                [invoice.id]: event.target.value,
                              }))
                            }
                            style={{
                              padding: "9px",
                              border: "1px solid #cbd5e1",
                              borderRadius: "7px",
                              background: "#ffffff",
                            }}
                          >
                            <option value="UPI">UPI</option>
                            <option value="CASH">Cash</option>
                            <option value="CARD">Card</option>
                            <option value="BANK_TRANSFER">Bank Transfer</option>
                          </select>

                          <button
                            type="button"
                            onClick={() => handlePayment(invoice)}
                            disabled={loadingInvoice === invoice.id}
                            style={buttonStyle}
                          >
                            {loadingInvoice === invoice.id
                              ? "Processing..."
                              : "Record Payment"}
                          </button>
                        </div>
                      ) : invoice.status === "PAID" ? (
                        <span style={{ color: "#0f766e", fontWeight: 600 }}>
                          Payment complete
                        </span>
                      ) : (
                        <span style={{ color: "#64748b" }}>
                          Check invoice total
                        </span>
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
