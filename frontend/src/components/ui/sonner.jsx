import { Toaster as Sonner, toast } from "sonner"

const Toaster = ({
  ...props
}) => {
  return (
    <Sonner
      theme="dark"
      position="top-right"
      className="toaster group"
      style={{ zIndex: 99999 }}
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-slate-800 group-[.toaster]:text-white group-[.toaster]:border-slate-700 group-[.toaster]:shadow-xl",
          description: "group-[.toast]:text-slate-400",
          actionButton:
            "group-[.toast]:bg-cyan-500 group-[.toast]:text-white",
          cancelButton:
            "group-[.toast]:bg-slate-700 group-[.toast]:text-slate-300",
          success: "group-[.toaster]:bg-green-900/90 group-[.toaster]:border-green-700",
          error: "group-[.toaster]:bg-red-900/90 group-[.toaster]:border-red-700",
          warning: "group-[.toaster]:bg-amber-900/90 group-[.toaster]:border-amber-700",
          info: "group-[.toaster]:bg-blue-900/90 group-[.toaster]:border-blue-700",
        },
        style: {
          zIndex: 99999,
        }
      }}
      {...props} />
  );
}

export { Toaster, toast }
