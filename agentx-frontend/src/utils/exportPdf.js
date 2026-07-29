import html2pdf from 'html2pdf.js';

export function downloadPdf({ title, subtitle, sections, filename = 'export.pdf' }) {
  const container = document.createElement('div');
  container.style.padding = '24px';
  container.style.fontFamily = 'Arial, sans-serif';
  // PDF should always be light theme regardless of app mode
  container.style.color = '#0f172a';
  container.style.backgroundColor = '#ffffff';

  const sectionsHtml = sections
    .map((section) => {
      let contentHtml = '';

      if (typeof section.content === 'string') {
        contentHtml = `<p style="margin: 0; line-height: 1.6; color: #334155; white-space: pre-wrap; font-size: 14px;">${section.content || 'N/A'}</p>`;
      } else if (Array.isArray(section.content)) {
        if (!section.content || section.content.length === 0) {
          contentHtml = `<p style="margin: 0; color: #94a3b8; font-style: italic; font-size: 14px;">No items available.</p>`;
        } else {
          const listItems = section.content
            .map((item) => {
              const text = typeof item === 'object' ? JSON.stringify(item) : item;
              return `<li style="margin-bottom: 8px; padding: 10px 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; color: #1e293b; line-height: 1.5; font-size: 14px;">${text}</li>`;
            })
            .join('');
          contentHtml = `<ul style="list-style: none; padding: 0; margin: 0;">${listItems}</ul>`;
        }
      }

      return `
        <div style="margin-bottom: 24px; page-break-inside: avoid;">
          <h2 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 700; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px;">
            ${section.title}
          </h2>
          ${section.subtitle ? `<p style="margin: 0 0 12px 0; font-size: 12px; color: #64748b;">${section.subtitle}</p>` : ''}
          ${contentHtml}
        </div>
      `;
    })
    .join('');

  container.innerHTML = `
    <div style="border-bottom: 3px solid #0284c7; padding-bottom: 16px; margin-bottom: 24px;">
      <h1 style="margin: 0 0 6px 0; font-size: 24px; color: #0f172a;">${title}</h1>
      ${subtitle ? `<p style="margin: 0; font-size: 13px; color: #64748b;">${subtitle}</p>` : ''}
      <p style="margin-top: 8px; font-size: 11px; color: #94a3b8;">Generated on ${new Date().toLocaleString()}</p>
    </div>
    <div>${sectionsHtml}</div>
    <div style="margin-top: 40px; padding-top: 12px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 11px; color: #94a3b8;">
      AgentX Report &bull; Generated Automatically
    </div>
  `;

  const opt = {
    margin: [10, 10, 10, 10],
    filename: filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
  };

  try {
    html2pdf().set(opt).from(container).save();
  } catch (e) {
    console.error('html2pdf failed, falling back to print window:', e);
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`<html><head><title>${title}</title></head><body>${container.innerHTML}<script>window.onload=function(){window.print();window.close();}</script></body></html>`);
      printWindow.document.close();
    }
  }
}
export function shareViaEmail({ subject, body, to = "" }) {
  let emailBody = body;
  try {
    const parsed = JSON.parse(body);
    emailBody = JSON.stringify(parsed, null, 2);
  } catch (e) {
    // not JSON, keep as is
  }
  const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(to)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(emailBody)}`;
  const a = document.createElement('a');
  a.href = gmailUrl;
  a.target = '_blank';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

}
