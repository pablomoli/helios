import { Sun, Mic, Zap, Code, Lightbulb, Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const features = [
  {
    icon: Sun,
    title: "Smart Solar Tracking",
    description: "Advanced light sensors and dual motors work together to dynamically rotate the solar panel toward the brightest sunlight, maximizing energy capture throughout the day.",
    color: "text-primary",
  },
  {
    icon: Mic,
    title: "Voice-Powered Control",
    description: "Seamlessly command Helios AI with your voice using Google Gemini API. Make solar adjustments hands-free and intuitive with natural language commands.",
    color: "text-secondary",
  },
  {
    icon: Code,
    title: "Arduino Innovation",
    description: "Built on Arduino with custom firmware, our robot showcases efficient embedded systems programming and precise motor control for optimal solar tracking.",
    color: "text-accent",
  },
  {
    icon: Zap,
    title: "Maximum Efficiency",
    description: "Real-time solar optimization ensures peak energy generation. Our dual-axis tracking system captures up to 40% more energy than fixed panels.",
    color: "text-primary",
  },
  {
    icon: Lightbulb,
    title: "AI-Powered Intelligence",
    description: "Google Gemini AI integration enables natural conversations about solar data, system status, and environmental conditions with contextual understanding.",
    color: "text-secondary",
  },
  {
    icon: Users,
    title: "Student-Built Innovation",
    description: "Designed, coded, and assembled by our passionate team of college students for this hackathon. A testament to what determination and creativity can achieve.",
    color: "text-accent",
  },
];

const Features = () => {
  return (
    <section className="py-24 px-4 bg-gradient-to-b from-background to-muted/30">
      <div className="container">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold">
            Innovation Meets Sustainability
          </h2>
          <p className="text-lg text-muted-foreground">
            Helios AI combines cutting-edge technology with environmental consciousness, 
            creating a smarter way to harness solar energy.
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card 
                key={index}
                className="group hover:shadow-glow transition-smooth border-2 hover:border-primary/50 bg-card/50 backdrop-blur"
              >
                <CardContent className="p-6 space-y-4">
                  <div className={`inline-flex p-3 rounded-2xl bg-gradient-to-br from-primary/10 to-secondary/10 ${feature.color} group-hover:scale-110 transition-smooth`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold group-hover:text-primary transition-smooth">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;
