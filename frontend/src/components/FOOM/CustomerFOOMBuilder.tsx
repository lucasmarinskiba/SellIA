/**
 * Customer FOOM Campaign Builder
 * No-code interface for creating FOOM campaigns
 */

import React, { useState, useEffect } from 'react';

interface Template {
  id: string;
  name: string;
  description: string;
  conversion_lift: string;
  setup_time: string;
  icon: string;
}

interface CampaignConfig {
  templateType: string;
  campaignName: string;
  startDate: string;
  endDate: string;
  messageOverrides: Record<string, string>;
  colorScheme: { primary: string; secondary: string };
  enabledWidgets: string[];
}

export const CustomerFOOMBuilder: React.FC = () => {
  const [step, setStep] = useState<'template-select' | 'configuration' | 'preview' | 'deployment'>(
    'template-select'
  );
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [config, setConfig] = useState<CampaignConfig>({
    templateType: '',
    campaignName: '',
    startDate: new Date().toISOString().split('T')[0],
    endDate: '',
    messageOverrides: {},
    colorScheme: { primary: '#FF6B6B', secondary: '#4ECDC4' },
    enabledWidgets: [],
  });
  const [embedCode, setEmbedCode] = useState('');
  const [campaignId, setCampaignId] = useState('');

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch('/fomo/customer/templates');
      const data = await res.json();
      setTemplates(data.templates);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId);
    setConfig({ ...config, templateType: templateId });
    setStep('configuration');
  };

  const handleConfigUpdate = (key: keyof CampaignConfig, value: any) => {
    setConfig({ ...config, [key]: value });
  };

  const handleContinue = async () => {
    if (step === 'configuration') {
      setStep('preview');
    } else if (step === 'preview') {
      await handleDeploy();
    }
  };

  const handleDeploy = async () => {
    try {
      const res = await fetch('/fomo/customer/campaigns/from-template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_type: config.templateType,
          business_id: localStorage.getItem('business_id'),
          custom_config: {
            name: config.campaignName,
            start_date: config.startDate,
            end_date: config.endDate,
            messaging: config.messageOverrides,
            color_scheme: config.colorScheme,
            enabled_widgets: config.enabledWidgets,
          },
        }),
      });

      if (!res.ok) throw new Error('Failed to create campaign');
      const campaign = await res.json();
      setCampaignId(campaign.campaign_id);

      // Generate embed code
      const embedRes = await fetch(`/fomo/customer/widgets/generate-embed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: campaign.campaign_id,
          widget_type: config.enabledWidgets[0] || 'visitor_counter',
        }),
      });

      if (embedRes.ok) {
        const embedData = await embedRes.json();
        setEmbedCode(embedData.embed_code);
      }

      setStep('deployment');
    } catch (err) {
      console.error('Deployment failed:', err);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '24px' }}>
      {/* Step Indicator */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
          {['Template', 'Configure', 'Preview', 'Deploy'].map((label, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: i < ['template-select', 'configuration', 'preview', 'deployment'].indexOf(step)
                    ? '#10b981'
                    : step === ['template-select', 'configuration', 'preview', 'deployment'][i]
                      ? '#3b82f6'
                      : '#e5e7eb',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                }}
              >
                {i + 1}
              </div>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Step 1: Template Selection */}
      {step === 'template-select' && (
        <div>
          <h2 style={{ marginBottom: '24px' }}>Choose Your FOMO Campaign Template</h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '16px',
            }}
          >
            {templates.map((template) => (
              <div
                key={template.id}
                onClick={() => handleTemplateSelect(template.id)}
                style={{
                  padding: '20px',
                  border: selectedTemplate === template.id ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: selectedTemplate === template.id ? '#f0f9ff' : 'white',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>{template.icon}</div>
                <h3 style={{ marginBottom: '8px' }}>{template.name}</h3>
                <p style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
                  {template.description}
                </p>
                <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#999' }}>
                  <span>📈 {template.conversion_lift} lift</span>
                  <span>⏱️ {template.setup_time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Configuration */}
      {step === 'configuration' && (
        <div>
          <h2 style={{ marginBottom: '24px' }}>Configure Your Campaign</h2>
          <form
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
              maxWidth: '600px',
            }}
          >
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                Campaign Name
              </label>
              <input
                type="text"
                value={config.campaignName}
                onChange={(e) => handleConfigUpdate('campaignName', e.target.value)}
                placeholder="e.g., Summer Flash Sale"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                  Start Date
                </label>
                <input
                  type="date"
                  value={config.startDate}
                  onChange={(e) => handleConfigUpdate('startDate', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                  End Date
                </label>
                <input
                  type="date"
                  value={config.endDate}
                  onChange={(e) => handleConfigUpdate('endDate', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                Primary Color
              </label>
              <input
                type="color"
                value={config.colorScheme.primary}
                onChange={(e) =>
                  handleConfigUpdate('colorScheme', {
                    ...config.colorScheme,
                    primary: e.target.value,
                  })
                }
                style={{
                  width: '60px',
                  height: '40px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '12px', fontWeight: '600' }}>
                Enable Widgets
              </label>
              {['Visitor Counter', 'Purchase Feed', 'Countdown Timer', 'Stock Badge'].map(
                (widget, i) => (
                  <label
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '8px',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      onChange={(e) => {
                        const newWidgets = e.target.checked
                          ? [...config.enabledWidgets, widget.toLowerCase()]
                          : config.enabledWidgets.filter((w) => w !== widget.toLowerCase());
                        handleConfigUpdate('enabledWidgets', newWidgets);
                      }}
                    />
                    {widget}
                  </label>
                )
              )}
            </div>

            <button
              onClick={() => setStep('preview')}
              style={{
                padding: '12px 24px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '600',
              }}
            >
              Continue to Preview
            </button>
          </form>
        </div>
      )}

      {/* Step 3: Preview */}
      {step === 'preview' && (
        <div>
          <h2 style={{ marginBottom: '24px' }}>Preview Your Campaign</h2>
          <div
            style={{
              padding: '24px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              backgroundColor: '#f9fafb',
              marginBottom: '24px',
            }}
          >
            <p>
              <strong>Campaign:</strong> {config.campaignName}
            </p>
            <p>
              <strong>Template:</strong> {selectedTemplate}
            </p>
            <p>
              <strong>Period:</strong> {config.startDate} to {config.endDate || 'Ongoing'}
            </p>
            <p>
              <strong>Widgets:</strong> {config.enabledWidgets.join(', ') || 'None selected'}
            </p>
            <p>
              <strong>Primary Color:</strong>{' '}
              <span
                style={{
                  display: 'inline-block',
                  width: '20px',
                  height: '20px',
                  backgroundColor: config.colorScheme.primary,
                  borderRadius: '4px',
                }}
              />
            </p>
          </div>
          <button
            onClick={handleDeploy}
            style={{
              padding: '12px 24px',
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '600',
            }}
          >
            Deploy Campaign
          </button>
        </div>
      )}

      {/* Step 4: Deployment */}
      {step === 'deployment' && (
        <div>
          <h2 style={{ marginBottom: '24px', color: '#10b981' }}>✅ Campaign Deployed!</h2>
          <div
            style={{
              padding: '24px',
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '8px',
              marginBottom: '24px',
            }}
          >
            <p style={{ marginBottom: '16px', fontWeight: '600' }}>Campaign ID: {campaignId}</p>
            <p style={{ marginBottom: '16px' }}>Copy this code and paste into your website:</p>
            <div
              style={{
                backgroundColor: '#1f2937',
                color: '#10b981',
                padding: '16px',
                borderRadius: '6px',
                fontFamily: 'monospace',
                fontSize: '12px',
                overflowX: 'auto',
                marginBottom: '16px',
              }}
            >
              {embedCode}
            </div>
            <button
              onClick={() => navigator.clipboard.writeText(embedCode)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              Copy Code
            </button>
          </div>

          <div style={{ textAlign: 'center' }}>
            <p style={{ marginBottom: '16px', color: '#666' }}>Need help embedding?</p>
            <a
              href={`/fomo/customer/widgets/visitor_counter/guide`}
              style={{
                color: '#3b82f6',
                textDecoration: 'none',
                fontWeight: '600',
              }}
            >
              View Embedding Guide
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerFOOMBuilder;
