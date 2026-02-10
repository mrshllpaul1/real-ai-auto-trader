/**
 * Export Data Button Component
 * Provides UI for exporting trades, portfolio, and performance data
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Download, FileSpreadsheet, FileJson, FileText, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

/**
 * Export button with dropdown menu
 */
export const ExportButton = ({ 
  userId = 'demo_user',
  exportType = 'trades', // 'trades', 'portfolio', 'performance', 'tax'
  variant = 'default',
  size = 'default',
  className = ''
}) => {
  const [showDialog, setShowDialog] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleQuickExport = async (format) => {
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
    let endpoint = '';

    switch (exportType) {
      case 'trades':
        endpoint = `/api/export/trades/${format}?user_id=${userId}`;
        break;
      case 'portfolio':
        endpoint = `/api/export/portfolio/${format}?user_id=${userId}`;
        break;
      case 'performance':
        endpoint = `/api/export/performance/report?user_id=${userId}&format=${format}`;
        break;
      default:
        endpoint = `/api/export/trades/${format}?user_id=${userId}`;
    }

    const url = `${baseUrl}${endpoint}`;
    
    try {
      toast.loading(`Exporting ${exportType} to ${format.toUpperCase()}...`);
      
      // Open in new tab to trigger download
      window.open(url, '_blank');
      
      setTimeout(() => {
        toast.success(`${exportType.charAt(0).toUpperCase() + exportType.slice(1)} exported successfully!`);
      }, 1000);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Export failed. Please try again.');
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant={variant} size={size} className={className}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuLabel>Export Format</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => handleQuickExport('csv')}>
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            Export as CSV
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleQuickExport('json')}>
            <FileJson className="h-4 w-4 mr-2" />
            Export as JSON
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setShowDialog(true)}>
            <FileText className="h-4 w-4 mr-2" />
            Advanced Export...
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AdvancedExportDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        userId={userId}
        exportType={exportType}
      />
    </>
  );
};

/**
 * Advanced export dialog with filters
 */
const AdvancedExportDialog = ({ open, onOpenChange, userId, exportType }) => {
  const [format, setFormat] = useState('csv');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [strategy, setStrategy] = useState('');
  const [coin, setCoin] = useState('');
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
    
    // Build query params
    const params = new URLSearchParams({ user_id: userId });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (strategy) params.append('strategy', strategy);
    if (coin) params.append('coin', coin);

    let endpoint = '';
    switch (exportType) {
      case 'trades':
        endpoint = `/api/export/trades/${format}`;
        break;
      case 'portfolio':
        endpoint = `/api/export/portfolio/${format}`;
        break;
      case 'performance':
        params.append('format', format);
        endpoint = `/api/export/performance/report`;
        break;
      default:
        endpoint = `/api/export/trades/${format}`;
    }

    const url = `${baseUrl}${endpoint}?${params.toString()}`;
    
    try {
      toast.loading('Preparing export...');
      
      // Open in new tab to trigger download
      window.open(url, '_blank');
      
      setTimeout(() => {
        toast.success('Export started! Check your downloads.');
        setExporting(false);
        onOpenChange(false);
      }, 1000);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Export failed. Please try again.');
      setExporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Advanced Export Options</DialogTitle>
          <DialogDescription>
            Customize your export with filters and options
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Format Selection */}
          <div className="space-y-2">
            <Label>Export Format</Label>
            <Select value={format} onValueChange={setFormat}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV (Excel compatible)</SelectItem>
                <SelectItem value="json">JSON (API integration)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Date Range (for trades) */}
          {exportType === 'trades' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Start Date</Label>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>End Date</Label>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </div>

              {/* Filter by Strategy */}
              <div className="space-y-2">
                <Label>Filter by Strategy (Optional)</Label>
                <Input
                  placeholder="e.g., ai_momentum, manual"
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                />
              </div>

              {/* Filter by Coin */}
              <div className="space-y-2">
                <Label>Filter by Coin (Optional)</Label>
                <Input
                  placeholder="e.g., BTC, ETH, SOL"
                  value={coin}
                  onChange={(e) => setCoin(e.target.value)}
                />
              </div>
            </>
          )}

          {/* Info message */}
          <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-md">
            <CheckCircle2 className="h-4 w-4 inline mr-2" />
            Your export will download automatically
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={exporting}>
            {exporting ? 'Exporting...' : 'Export'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Tax report export button
 */
export const TaxReportButton = ({ userId = 'demo_user', className = '' }) => {
  const [year, setYear] = useState(new Date().getFullYear());
  const [showDialog, setShowDialog] = useState(false);

  const handleExport = (format) => {
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
    const url = `${baseUrl}/api/export/tax-report?user_id=${userId}&tax_year=${year}&format=${format}`;
    
    toast.loading(`Generating ${year} tax report...`);
    window.open(url, '_blank');
    
    setTimeout(() => {
      toast.success(`Tax report for ${year} ready!`);
      setShowDialog(false);
    }, 1000);
  };

  return (
    <>
      <Button variant="outline" onClick={() => setShowDialog(true)} className={className}>
        <FileText className="h-4 w-4 mr-2" />
        Tax Report
      </Button>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Export Tax Report</DialogTitle>
            <DialogDescription>
              Generate a tax report for a specific year
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Tax Year</Label>
              <Input
                type="number"
                min="2020"
                max={new Date().getFullYear()}
                value={year}
                onChange={(e) => setYear(parseInt(e.target.value))}
              />
            </div>

            <p className="text-sm text-muted-foreground">
              This report includes all trades from January 1 to December 31, {year}.
              Compatible with tax software like TurboTax.
            </p>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => handleExport('csv')}>
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            <Button onClick={() => handleExport('json')}>
              <FileJson className="h-4 w-4 mr-2" />
              Export JSON
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ExportButton;
