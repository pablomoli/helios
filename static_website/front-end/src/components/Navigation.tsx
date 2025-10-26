import { Button } from "@/components/ui/button";
import { Sun, Menu } from "lucide-react";

const Navigation = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
      <div className="container px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg gradient-solar">
              <Sun className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">Helios AI</span>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm font-medium hover:text-primary transition-smooth">
              Features
            </a>
            <a href="#journey" className="text-sm font-medium hover:text-primary transition-smooth">
              Journey
            </a>
            <a href="#demo" className="text-sm font-medium hover:text-primary transition-smooth">
              Demo
            </a>
            <Button variant="hero" size="sm">
              Try Voice Control
            </Button>
          </div>
          
          {/* Mobile Menu Button */}
          <Button variant="ghost" size="icon" className="md:hidden">
            <Menu className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
