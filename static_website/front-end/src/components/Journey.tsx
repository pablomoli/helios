import { Card, CardContent } from "@/components/ui/card";
import { Calendar, Users, Lightbulb, Rocket } from "lucide-react";
import solarPattern from "@/assets/solar-pattern.jpg";

const milestones = [
  {
    icon: Lightbulb,
    title: "The Idea",
    description: "Brainstormed a solar-tracking robot that could maximize energy efficiency while being controlled by voice commands.",
  },
  {
    icon: Users,
    title: "Team Assembly",
    description: "Brought together passionate college students with diverse skills in engineering, programming, and design.",
  },
  {
    icon: Calendar,
    title: "Hackathon Build",
    description: "Intensive coding sessions, hardware assembly, and integration of Arduino with Google Gemini API over the hackathon weekend.",
  },
  {
    icon: Rocket,
    title: "Launch & Demo",
    description: "Successfully demonstrated Helios AI's capabilities with live solar tracking and voice control at the hackathon.",
  },
];

const Journey = () => {
  return (
    <section className="py-24 px-4 relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-5">
        <img 
          src={solarPattern} 
          alt="" 
          className="w-full h-full object-cover"
        />
      </div>
      
      <div className="container relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-4xl md:text-5xl font-bold">
              Our Hackathon Journey
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              From concept to reality in one intense weekend. Here's how we built 
              Helios AI from the ground up.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 mb-16">
            {milestones.map((milestone, index) => {
              const Icon = milestone.icon;
              return (
                <Card 
                  key={index}
                  className="group hover:shadow-soft transition-smooth border-2 hover:border-primary/30 bg-card/80 backdrop-blur"
                >
                  <CardContent className="p-6 flex gap-4">
                    <div className="flex-shrink-0">
                      <div className="p-3 rounded-xl gradient-solar text-white group-hover:scale-110 transition-smooth">
                        <Icon className="w-6 h-6" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-xl font-semibold">
                        {milestone.title}
                      </h3>
                      <p className="text-muted-foreground">
                        {milestone.description}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
          
          {/* Story section */}
          <Card className="bg-gradient-to-br from-card to-muted/30 border-2 border-primary/20">
            <CardContent className="p-8 md:p-12 space-y-6">
              <h3 className="text-2xl md:text-3xl font-bold">
                Built by Students, Powered by Passion
              </h3>
              <div className="prose prose-lg max-w-none text-muted-foreground space-y-4">
                <p>
                  We're a team of college students passionate about sustainability and technology. 
                  Helios AI is our hackathon project that combines Arduino hardware, intelligent 
                  light sensors, and Google's Gemini AI to create something truly innovative.
                </p>
                <p>
                  Our robot uses dual motors and advanced sensors to automatically track the sun's 
                  position throughout the day, ensuring maximum energy capture from the solar panel. 
                  The integration with Google Gemini API allows for natural voice commands, making 
                  solar energy management intuitive and accessible.
                </p>
                <p>
                  This project represents countless hours of coding, testing, and iteration. 
                  It's a testament to what students can achieve when we combine technical skills 
                  with environmental consciousness and creative problem-solving.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default Journey;
