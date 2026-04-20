import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const xlsx = '/Users/nikolajtamrazov/Documents/BACKUP_GOLD/output/office_control/STROYSTANDART_Office_Accounting.xlsx';
const blob = await FileBlob.load(xlsx);
const wb = await SpreadsheetFile.importXlsx(blob);

const overview = await wb.inspect({
  kind: 'workbook',
  include: 'names,sheets',
});
console.log('---WORKBOOK---');
console.log(overview.ndjson);

const contracts = await wb.inspect({
  kind: 'table',
  range: 'Contracts!A1:K12',
  include: 'values,formulas',
  tableMaxRows: 12,
  tableMaxCols: 11,
});
console.log('---CONTRACTS---');
console.log(contracts.ndjson);

const errors = await wb.inspect({
  kind: 'match',
  searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A',
  options: { useRegex: true, maxResults: 200 },
  summary: 'formula_error_scan',
});
console.log('---ERRORS---');
console.log(errors.ndjson);
