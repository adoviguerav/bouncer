# Common Patterns

## API Response Format

```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}
```

## Custom Hooks Pattern

```typescript
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}
```

## Repository Pattern

```typescript
interface Repository<T> {
  findAll(filters?: Filters): Promise<T[]>
  findById(id: string): Promise<T | null>
  create(data: CreateDto): Promise<T>
  update(id: string, data: UpdateDto): Promise<T>
  delete(id: string): Promise<void>
}
```

## Tailwind CSS v4 Patterns

### 1. CSS-First Configuration
```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --color-brand-500: #570df8;
  --spacing-custom: 2.5rem;
  --animate-bounce-slow: bounce 2s infinite;
}
```

### 2. Custom Utilities
```css
@utility btn-gradient {
  background: linear-gradient(45deg, #570df8, #a855f7);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
}
```

### 3. No More tailwind.config.js
- All configuration goes in CSS using `@theme`
- Use `@tailwindcss/postcss` plugin in PostCSS config
- DaisyUI themes are configured in CSS, not JS

## Supabase Patterns

### 1. Server Components (Most Common)
```typescript
import { createClient } from "@/libs/supabase/server";
import { redirect } from "next/navigation";

export default async function PrivatePage() {
  const supabase = await createClient(); // Always await!

  const { data: { user }, error } = await supabase.auth.getUser();

  if (!user) {
    redirect("/signin");
  }

  return <div>Protected content</div>;
}
```

### 2. Client Components
```typescript
"use client";
import { createClient } from "@/libs/supabase/client";
import { useEffect, useState } from "react";

export default function ClientComponent() {
  const supabase = createClient(); // No await needed on client
  const [user, setUser] = useState(null);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);
    };
    getUser();
  }, []);
}
```

### 3. API Routes
```typescript
import { createClient } from "@/libs/supabase/server";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const supabase = await createClient(); // Always await!

  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Your logic here
}
```

## Component Patterns

### 1. Server Component (Default)
```typescript
// No "use client" directive
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Page Title",
};

export default async function Page() {
  // Can use await, fetch data, etc.
  return <div>Server component</div>;
}
```

### 2. Client Component (When Needed)
```typescript
"use client";
import { useState, useEffect } from "react";

export default function InteractiveComponent() {
  const [state, setState] = useState(false);

  return (
    <button onClick={() => setState(!state)}>
      {state ? "On" : "Off"}
    </button>
  );
}
```

## API Route Patterns

### 1. Webhook Handler (Stripe)
```typescript
import { headers } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.text();
  const headersList = await headers(); // Must await!
  const signature = headersList.get("stripe-signature");

  // Verify webhook signature
  // Handle webhook event
}
```

### 2. Protected API Route
```typescript
import { createClient } from "@/libs/supabase/server";

export async function POST(req: NextRequest) {
  const supabase = await createClient(); // Must await!

  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Protected logic here
}
```

## Styling Patterns

### 1. Use DaisyUI Components
```jsx
<div className="card bg-base-100 shadow-xl">
  <div className="card-body">
    <h2 className="card-title">Card Title</h2>
    <p>Card content</p>
    <div className="card-actions justify-end">
      <button className="btn btn-primary">Action</button>
    </div>
  </div>
</div>
```

### 2. Responsive Design
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <div className="p-4 bg-base-200 rounded-lg">Content</div>
</div>
```

### 3. Custom Styles with CSS Variables
```jsx
<div
  className="p-4 rounded-lg"
  style={{ backgroundColor: "var(--color-brand-500)" }}
>
  Content with custom color
</div>
```

## Error Handling Patterns

### 1. API Routes
```typescript
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    if (!body.email) {
      return NextResponse.json(
        { error: "Email is required" },
        { status: 400 }
      );
    }

    // Your logic
    return NextResponse.json({ success: true });

  } catch (error) {
    console.error("API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
```

### 2. Client Components
```typescript
"use client";
import { toast } from "react-hot-toast";

export default function Component() {
  const handleAction = async () => {
    try {
      const response = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: "example" }),
      });

      if (!response.ok) {
        throw new Error("Action failed");
      }

      toast.success("Action completed successfully!");

    } catch (error) {
      toast.error("Something went wrong");
      console.error(error);
    }
  };
}
```

## Common Mistakes to Avoid

### ❌ Don't Do This
```typescript
// Old Next.js 14 patterns
const params = { id: "123" }; // params should use await
const headers = headers(); // should be await headers()
const supabase = createClient(); // should be await createClient() on server

// Old Tailwind config
module.exports = { theme: { ... } }; // Should be CSS @theme

// Hardcoded values
const apiUrl = "https://api.example.com"; // Should use env vars
```

### ✅ Do This Instead
```typescript
// Next.js 15 patterns
const { id } = await params;
const headersList = await headers();
const supabase = await createClient();

// Tailwind v4 CSS config
@theme {
  --color-primary: #570df8;
}

// Environment variables
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

## File Structure to Follow
```
app/
├── api/
│   ├── auth/callback/route.ts
│   ├── stripe/
│   │   ├── create-checkout/route.ts
│   │   └── create-portal/route.ts
│   └── webhook/stripe/route.ts
├── blog/[articleId]/page.tsx
├── dashboard/
│   ├── layout.tsx
│   └── page.tsx
├── globals.css
└── layout.tsx

components/
├── ButtonCheckout.tsx
├── ButtonSignin.tsx
└── LayoutClient.tsx

libs/
├── supabase/
│   ├── client.ts
│   └── server.ts
├── stripe.ts
└── resend.ts
```

## When to Use Each Pattern

### Use Server Components When:
- Fetching data from database/API
- Handling auth checks
- Generating metadata
- Rendering static content

### Use Client Components When:
- Handling user interactions (clicks, form inputs)
- Managing local state
- Using browser APIs
- Real-time features

### Use API Routes When:
- Handling form submissions
- Webhook endpoints
- Server-side operations
- Database mutations

## Testing Considerations

### Build Test Command
Always test that the project builds successfully:
```bash
npm run build
```

### Common Build Errors to Watch For:
1. Missing `await` on Next.js 15 async APIs
2. Incorrect typing of `params` on dynamic routes
3. Client/Server component boundary issues
4. Missing environment variables
5. Tailwind CSS config errors
