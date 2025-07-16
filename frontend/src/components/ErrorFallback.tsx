import React from "react";
import { Box, Paper, Typography, Button, Alert } from "@mui/material";
import { ErrorOutline, Refresh } from "@mui/icons-material";

interface ErrorFallbackProps {
  error?: Error;
  resetErrorBoundary?: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ 
  error, 
  resetErrorBoundary 
}) => {
  const handleReload = () => {
    window.location.reload();
  };

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        p: 2
      }}
    >
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          textAlign: 'center', 
          maxWidth: 500,
          width: '100%'
        }}
      >
        <ErrorOutline 
          sx={{ 
            fontSize: 64, 
            color: 'error.main', 
            mb: 2 
          }} 
        />
        
        <Typography variant="h4" component="h1" gutterBottom>
          Something went wrong
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          We're sorry, but something unexpected happened. Please try reloading the page.
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mt: 2, mb: 2, textAlign: 'left' }}>
            <Typography variant="body2" component="pre">
              {error.message}
            </Typography>
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
          {resetErrorBoundary && (
            <Button 
              variant="outlined" 
              onClick={resetErrorBoundary}
              startIcon={<Refresh />}
            >
              Try Again
            </Button>
          )}
          
          <Button 
            variant="contained" 
            onClick={handleReload}
            startIcon={<Refresh />}
          >
            Reload Page
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default ErrorFallback; 