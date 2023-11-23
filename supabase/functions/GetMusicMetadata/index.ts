import "https://deno.land/x/xhr@0.3.0/mod.ts";
import { CreateCompletionRequest } from "https://esm.sh/openai@3.1.0";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
const schema = {
  type: "object",
  properties: {
    artist_name: {
      type: "string",
      description: "Name of the artist",
    },
    event_name: {
      type: "string",
      description: "Name of the event",
    },
  },
};

serve(async (req) => {
  const json = await req.json();
  console.log(json);
  const { event_name, description } = json.record;
  const messages: { role: string; content: string }[] = [
    {
      role: "system",
      content: "Here is the description of a music event",
    },
    {
      role: "system",
      content: description,
    },
    {
      role: "system",
      content:
        "I'm going to give you the name of an event at a music venue, can you tell me the name of the artists playing at the event?",
    },
    {
      role: "system",
      content: `The event is  ${event_name}`,
    },
    {
      role: "system",
      content: `Can you format the artists names as json?
      {
        artists: [
          artistName: """Insert artist name here""",
        ]
      }`,
    },
  ];

  const completionConfig: CreateCompletionRequest = {
    model: "gpt-3.5-turbo",
    messages,
    // response_format: { type: "json_object" },
    // response_format={ "type": "json_object" },
    max_tokens: 256,
    temperature: 0,

    // stream: true,
  };
  const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY");
  const aiResponse = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(completionConfig),
  });
  const aiJson = await aiResponse.json();
  console.log(aiJson);
  const { artists } = JSON.parse(aiJson.choices[0].message.content);
  console.log("artists", artists);
  const output = {
    eventName: event_name,
    artists,
  };
  return new Response(JSON.stringify(output), {
    headers: { "Content-Type": "application/json" },
  });
});
