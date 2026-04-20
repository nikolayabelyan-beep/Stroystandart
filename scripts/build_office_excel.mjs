import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const ROOT = '/Users/nikolajtamrazov/Documents/BACKUP_GOLD';
const CONTRACTS_PATH = path.join(ROOT, 'obsidian_vault', 'MASTER_CONTRACTS.md');
const COMPANY_PATH = path.join(ROOT, 'obsidian_vault', 'MY_COMPANY.md');
const OUTPUT_DIR = path.join(ROOT, 'output', 'office_control');
const OUTPUT_XLSX = path.join(OUTPUT_DIR, 'STROYSTANDART_Office_Accounting.xlsx');

function cleanText(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}

function parseMoney(ruMoney) {
  const normalized = (ruMoney || '')
    .replace(/₽/g, '')
    .replace(/\s/g, '')
    .replace(',', '.')
    .trim();
  const n = Number(normalized);
  return Number.isFinite(n) ? n : 0;
}

function parseDateRu(dateText) {
  const m = (dateText || '').match(/(\d{2})\.(\d{2})\.(\d{4})/);
  if (!m) return null;
  return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function captureField(block, fieldLabel) {
  const safeLabel = escapeRegExp(fieldLabel);
  const re = new RegExp(`\\*\\s*\\*\\*${safeLabel}:\\*\\*\\s*(.+)`);
  const m = block.match(re);
  return cleanText(m ? m[1] : '');
}

function parseContracts(md) {
  const blocks = [...md.matchAll(/###\s+\d+\.\s+Объект:\s+(.+?)\n([\s\S]*?)(?=\n---|\n###\s+\d+\.|$)/g)];
  return blocks.map(([, objectNameRaw, block], idx) => {
    const objectName = cleanText(objectNameRaw);
    const customer = captureField(block, 'Заказчик (Полное)');
    const contractInfo = captureField(block, 'Контракт');
    const noticeNo = captureField(block, 'Номер извещения');
    const works = captureField(block, 'Работы');
    const priceText = captureField(block, 'Цена контракта');
    const deadlineText = captureField(block, 'Срок исполнения');

    const contractNo = cleanText(contractInfo.replace(/^№\s*/i, '').replace(/\s+от\s+\d{2}\.\d{2}\.\d{4}$/i, ''));
    const contractDate = parseDateRu(contractInfo);

    return {
      id: idx + 1,
      objectName,
      customer,
      contractNo,
      contractDate,
      noticeNo,
      works,
      price: parseMoney(priceText),
      deadline: parseDateRu(deadlineText),
    };
  });
}

function parseCompany(md) {
  const lines = md.split(/\r?\n/);
  const pairs = [];
  for (const line of lines) {
    const m = line.match(/^\*\s+\*\*(.+?):\*\*\s*(.+)$/);
    if (m) {
      pairs.push([cleanText(m[1]), cleanText(m[2])]);
    }
  }
  return pairs;
}

function monthStartDates(year) {
  const dates = [];
  for (let m = 0; m < 12; m += 1) {
    dates.push(new Date(year, m, 1));
  }
  return dates;
}

async function main() {
  const contractsMd = await fs.readFile(CONTRACTS_PATH, 'utf8');
  const companyMd = await fs.readFile(COMPANY_PATH, 'utf8');
  const contracts = parseContracts(contractsMd);
  const companyPairs = parseCompany(companyMd);

  const workbook = Workbook.create();
  const dashboard = workbook.worksheets.add('Dashboard');
  const contractsSheet = workbook.worksheets.add('Contracts');
  const payments = workbook.worksheets.add('Payments');
  const expenses = workbook.worksheets.add('Expenses');
  const cashflow = workbook.worksheets.add('Cashflow');
  const company = workbook.worksheets.add('Company');

  dashboard.getRange('A1').value = 'STROYSTANDART Office Accounting Dashboard';
  dashboard.getRange('A3:B8').values = [
    ['Total contracts', '=COUNTA(Contracts!A2:A999)'],
    ['Total contract amount', '=SUM(Contracts!F2:F999)'],
    ['Total incoming payments', '=SUMIFS(Payments!E:E,Payments!F:F,"IN")'],
    ['Remaining receivable', '=B4-B5'],
    ['Overdue active contracts', '=COUNTIFS(Contracts!J2:J999,"Overdue")'],
    ['This month net cashflow', '=IFERROR(INDEX(Cashflow!D:D,MATCH(EOMONTH(TODAY(),-1)+1,Cashflow!A:A,0)),0)'],
  ];

  contractsSheet.getRange('A1:K1').values = [[
    'ID',
    'Object',
    'Customer',
    'Contract No',
    'Notice No',
    'Contract Amount',
    'Deadline',
    'Paid',
    'Remaining',
    'Status',
    'Work Scope',
  ]];

  if (contracts.length > 0) {
    const rows = contracts.map((c) => [
      c.id,
      c.objectName,
      c.customer,
      c.contractNo,
      c.noticeNo,
      c.price,
      c.deadline,
      null,
      null,
      null,
      c.works,
    ]);

    const endRow = 1 + rows.length;
    contractsSheet.getRange(`A2:K${endRow}`).values = rows;
    contractsSheet.getRange(`H2:H${endRow}`).formulas = rows.map((r) => [`=IFERROR(SUMIFS(Payments!$E:$E,Payments!$B:$B,D${r[0] + 1},Payments!$F:$F,"IN"),0)`]);
    contractsSheet.getRange(`I2:I${endRow}`).formulas = rows.map((r) => [`=F${r[0] + 1}-H${r[0] + 1}`]);
    contractsSheet.getRange(`J2:J${endRow}`).formulas = rows.map((r) => [`=IF(I${r[0] + 1}<=0,"Closed",IF(G${r[0] + 1}<TODAY(),"Overdue","In progress"))`]);
  }

  payments.getRange('A1:F1').values = [[
    'Date',
    'Contract No',
    'Type',
    'Description',
    'Amount',
    'Direction',
  ]];
  payments.getRange('A2:F6').values = [
    [null, null, 'Advance', 'Initial payment from customer', null, 'IN'],
    [null, null, 'Interim', 'KS-2/KS-3 payment', null, 'IN'],
    [null, null, 'Final', 'Final settlement', null, 'IN'],
    [null, null, 'Penalty', 'Penalty or adjustment', null, 'OUT'],
    [null, null, 'Other', 'Manual record', null, 'IN'],
  ];

  expenses.getRange('A1:E1').values = [[
    'Date',
    'Category',
    'Description',
    'Amount',
    'Direction',
  ]];
  expenses.getRange('A2:E7').values = [
    [null, 'Payroll', 'Salary payment', null, 'OUT'],
    [null, 'Materials', 'Material purchase', null, 'OUT'],
    [null, 'Subcontract', 'Subcontractor payment', null, 'OUT'],
    [null, 'Transport', 'Fuel and logistics', null, 'OUT'],
    [null, 'Taxes', 'Tax payment', null, 'OUT'],
    [null, 'Other', 'Other operating expense', null, 'OUT'],
  ];

  const year = new Date().getFullYear();
  const months = monthStartDates(year);
  cashflow.getRange('A1:E1').values = [[
    'Month',
    'Incoming',
    'Outgoing',
    'Net',
    'Cumulative',
  ]];
  cashflow.getRange('A2:A13').values = months.map((d) => [d]);
  cashflow.getRange('B2:B13').formulas = months.map((_, i) => [
    `=SUMIFS(Payments!$E:$E,Payments!$A:$A,">="&A${i + 2},Payments!$A:$A,"<"&EDATE(A${i + 2},1),Payments!$F:$F,"IN")`,
  ]);
  cashflow.getRange('C2:C13').formulas = months.map((_, i) => [
    `=SUMIFS(Expenses!$D:$D,Expenses!$A:$A,">="&A${i + 2},Expenses!$A:$A,"<"&EDATE(A${i + 2},1),Expenses!$E:$E,"OUT")+SUMIFS(Payments!$E:$E,Payments!$A:$A,">="&A${i + 2},Payments!$A:$A,"<"&EDATE(A${i + 2},1),Payments!$F:$F,"OUT")`,
  ]);
  cashflow.getRange('D2:D13').formulas = months.map((_, i) => [`=B${i + 2}-C${i + 2}`]);
  cashflow.getRange('E2').formula = '=D2';
  cashflow.getRange('E3:E13').formulas = months.slice(1).map((_, i) => [`=E${i + 2}+D${i + 3}`]);

  company.getRange('A1:B1').values = [['Field', 'Value']];
  if (companyPairs.length > 0) {
    company.getRange(`A2:B${companyPairs.length + 1}`).values = companyPairs;
  }

  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  const outFile = await SpreadsheetFile.exportXlsx(workbook);
  await outFile.save(OUTPUT_XLSX);

  console.log(`[OK] Workbook created: ${OUTPUT_XLSX}`);
  console.log(`[OK] Contracts loaded: ${contracts.length}`);
}

await main();
