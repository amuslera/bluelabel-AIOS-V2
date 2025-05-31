# CDN Setup Guide

This guide covers setting up a Content Delivery Network (CDN) for AIOS v2 to optimize static asset delivery and improve global performance.

## Recommended CDN Providers

### 1. Cloudflare (Recommended)
- Free tier available
- Global network with 200+ PoPs
- Built-in DDoS protection
- Automatic image optimization
- WebP conversion support

### 2. AWS CloudFront
- Tight integration with S3
- Pay-as-you-go pricing
- Advanced caching controls
- Lambda@Edge for custom logic

### 3. Fastly
- Real-time configuration
- Instant purging
- Advanced VCL scripting
- Premium performance

## Configuration Steps

### Cloudflare Setup

1. **Add your domain to Cloudflare**
   ```bash
   # DNS records to add
   Type: CNAME
   Name: cdn
   Content: your-origin.example.com
   Proxy status: Proxied (orange cloud)
   ```

2. **Configure Page Rules**
   ```
   # Static assets (cache forever)
   https://cdn.example.com/static/*
   - Cache Level: Cache Everything
   - Edge Cache TTL: 1 month
   - Browser Cache TTL: 1 month
   
   # API responses (no cache)
   https://api.example.com/*
   - Cache Level: Bypass
   - Security Level: High
   ```

3. **Enable optimizations**
   - Auto Minify: JavaScript, CSS, HTML
   - Brotli: On
   - HTTP/2: On
   - HTTP/3 (QUIC): On
   - Polish: Lossy (image optimization)
   - Mirage: On (mobile optimization)

### Next.js Static Export Configuration

```javascript
// next.config.js
module.exports = {
  output: 'export',
  images: {
    loader: 'custom',
    loaderFile: './cdn-loader.js',
  },
  assetPrefix: process.env.CDN_URL || '',
  compress: false, // Let CDN handle compression
}

// cdn-loader.js
export default function cdnLoader({ src, width, quality }) {
  const params = new URLSearchParams({
    url: src,
    w: width,
    q: quality || 75,
  })
  return `${process.env.CDN_URL}/image?${params}`
}
```

### Asset Versioning

```javascript
// utils/assetVersion.js
import crypto from 'crypto'
import fs from 'fs'

export function getAssetHash(filePath) {
  const content = fs.readFileSync(filePath)
  return crypto.createHash('md5').update(content).digest('hex').slice(0, 8)
}

export function versionedAsset(path) {
  if (process.env.NODE_ENV === 'production') {
    const hash = getAssetHash(path)
    return `${process.env.CDN_URL}${path}?v=${hash}`
  }
  return path
}
```

### Cache Headers Configuration

```nginx
# nginx.conf for origin server
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary "Accept-Encoding";
}

location ~* \.(html|json)$ {
    expires 1h;
    add_header Cache-Control "public, must-revalidate";
}

location /api {
    expires -1;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
}
```

### CDN Performance Monitoring

```javascript
// utils/cdnMetrics.js
class CDNMetrics {
  static measureResourceTiming() {
    const resources = performance.getEntriesByType('resource')
    const cdnResources = resources.filter(r => r.name.includes(process.env.CDN_URL))
    
    const metrics = cdnResources.map(resource => ({
      url: resource.name,
      duration: resource.duration,
      size: resource.transferSize,
      cacheHit: resource.transferSize === 0,
      protocol: resource.nextHopProtocol,
    }))
    
    return {
      totalResources: metrics.length,
      cacheHitRate: metrics.filter(m => m.cacheHit).length / metrics.length * 100,
      avgLoadTime: metrics.reduce((sum, m) => sum + m.duration, 0) / metrics.length,
      metrics
    }
  }
  
  static reportToAnalytics() {
    const metrics = this.measureResourceTiming()
    
    // Send to your analytics service
    if (window.gtag) {
      window.gtag('event', 'cdn_performance', {
        cache_hit_rate: metrics.cacheHitRate,
        avg_load_time: metrics.avgLoadTime,
        total_resources: metrics.totalResources
      })
    }
  }
}

// Initialize monitoring
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    setTimeout(() => CDNMetrics.reportToAnalytics(), 1000)
  })
}
```

## Deployment Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy-cdn.yml
name: Deploy Static Assets to CDN

on:
  push:
    branches: [main]
    paths:
      - 'apps/web/public/**'
      - 'apps/web/.next/**'

jobs:
  deploy-cdn:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build static assets
        run: |
          cd apps/web
          npm ci
          npm run build
          npm run export
      
      - name: Deploy to Cloudflare R2
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          command: r2 object put aios-static --file=./out --recursive
      
      - name: Purge CDN cache
        run: |
          curl -X POST "https://api.cloudflare.com/client/v4/zones/${{ secrets.CLOUDFLARE_ZONE_ID }}/purge_cache" \
            -H "Authorization: Bearer ${{ secrets.CLOUDFLARE_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            --data '{"purge_everything":true}'
```

### Environment Variables

```bash
# .env.production
CDN_URL=https://cdn.aios.example.com
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_API_TOKEN=your-api-token

# For development
CDN_URL=http://localhost:3000
```

## Performance Targets

- **First Byte Time**: < 50ms from edge
- **Static Asset Delivery**: < 100ms globally
- **Cache Hit Rate**: > 95%
- **Bandwidth Savings**: > 80%

## Monitoring Dashboard

Create a Cloudflare Analytics dashboard to track:
- Cache hit ratio
- Bandwidth saved
- Requests by geography
- Response time by region
- Top requested resources
- 4xx/5xx error rates

## Cost Optimization

1. **Optimize images before upload**
   ```bash
   # Install tools
   npm install -g imagemin-cli imagemin-webp
   
   # Optimize images
   imagemin public/images/* --out-dir=public/images/optimized
   imagemin public/images/* --plugin=webp --out-dir=public/images/webp
   ```

2. **Enable Cloudflare Polish**
   - Automatic WebP conversion
   - Lossy compression for smaller files
   - Adaptive image sizing

3. **Use appropriate cache headers**
   - Immutable assets: 1 year
   - HTML: 1 hour
   - API responses: No cache

## Troubleshooting

### Cache not updating
```bash
# Purge specific URL
curl -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://cdn.example.com/static/app.js"]}'
```

### CORS issues
```javascript
// Add CORS headers in Cloudflare Worker
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const response = await fetch(request)
  const newResponse = new Response(response.body, response)
  
  newResponse.headers.set('Access-Control-Allow-Origin', '*')
  newResponse.headers.set('Access-Control-Allow-Methods', 'GET, OPTIONS')
  
  return newResponse
}
```

## Security Considerations

1. **Enable Cloudflare WAF**
   - Block common attacks
   - Rate limiting
   - DDoS protection

2. **Restrict origin access**
   - Whitelist Cloudflare IPs only
   - Use authenticated origin pulls

3. **Enable DNSSEC**
   - Prevent DNS hijacking
   - Ensure content integrity

## Next Steps

1. Set up Cloudflare account
2. Configure DNS records
3. Update build process for CDN URLs
4. Test performance improvements
5. Monitor cache hit rates
6. Set up alerts for anomalies