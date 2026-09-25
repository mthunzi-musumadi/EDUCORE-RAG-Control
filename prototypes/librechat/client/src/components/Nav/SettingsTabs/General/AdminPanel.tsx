import { ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Label, Button } from '@librechat/client';
import { useLocalize } from '~/hooks';

export default function AdminPanel() {
  const localize = useLocalize();
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-between">
      <Label id="admin-panel-label">{localize('com_ui_admin_panel') || 'Admin Panel'}</Label>
      <Button
        variant="outline"
        onClick={() => {
          navigate('/admin');
        }}
      >
        <ShieldCheck className="size-4 mr-1.5 text-emerald-500 inline" aria-hidden="true" />
        <span>Open Admin Console</span>
      </Button>
    </div>
  );
}
