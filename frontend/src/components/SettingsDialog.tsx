import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  FormControlLabel,
  Switch,
  Typography,
  Box,
} from '@mui/material';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onClose }) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Settings</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Audio Settings
          </Typography>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Enable Voice Activity Detection"
            />
          </FormControl>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Noise Suppression"
            />
          </FormControl>
        </Box>
        
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Chat Settings
          </Typography>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Auto-scroll to new messages"
            />
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onClose} variant="contained">
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SettingsDialog; 