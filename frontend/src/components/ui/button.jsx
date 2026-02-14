import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 active:scale-[0.98] hover:scale-[1.02]",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90 hover:shadow-md",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90 hover:shadow-md",
        outline:
          "border border-input shadow-sm hover:bg-accent hover:text-accent-foreground hover:border-accent",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        // New enhanced variants
        success:
          "bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-sm hover:from-green-600 hover:to-emerald-700 hover:shadow-lg hover:shadow-green-500/25",
        warning:
          "bg-gradient-to-r from-yellow-500 to-orange-500 text-white shadow-sm hover:from-yellow-600 hover:to-orange-600 hover:shadow-lg hover:shadow-orange-500/25",
        premium:
          "bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-sm hover:from-purple-600 hover:to-pink-600 hover:shadow-lg hover:shadow-purple-500/25",
        glow:
          "bg-primary text-primary-foreground shadow-lg shadow-primary/50 hover:shadow-xl hover:shadow-primary/60 animate-pulse hover:animate-none",
        glass:
          "bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 hover:border-white/30",
      },
      size: {
        default: "h-9 px-4 py-2",
        xs: "h-7 rounded px-2 text-xs",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        xl: "h-12 rounded-lg px-10 text-base",
        icon: "h-9 w-9",
        "icon-sm": "h-7 w-7",
        "icon-lg": "h-11 w-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ 
  className, 
  variant, 
  size, 
  asChild = false, 
  loading = false,
  loadingText,
  children,
  disabled,
  ...props 
}, ref) => {
  const Comp = asChild ? Slot : "button"
  const isDisabled = disabled || loading;
  
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      disabled={isDisabled}
      aria-busy={loading}
      aria-disabled={isDisabled}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          {loadingText || children}
        </>
      ) : (
        children
      )}
    </Comp>
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }
