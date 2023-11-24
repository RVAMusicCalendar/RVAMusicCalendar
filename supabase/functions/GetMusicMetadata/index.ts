import "https://deno.land/x/xhr@0.3.0/mod.ts";
import { CreateCompletionRequest } from "https://esm.sh/openai@3.1.0";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY");

serve(async (req) => {
  const authHeader = req.headers.get("Authorization")!;
  const supabaseClient = createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_ANON_KEY") ?? "",
    {
      global: {
        headers: {
          Authorization: `Bearer ${Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")}`,
        },
      },
    }
  );
  const json = await req.json();
  const { id, event_name, description } = json.record;
  const messages: { role: string; content: string }[] = [
    {
      role: "system",
      content: description,
    },
    {
      role: "system",
      content:
        "I'm going to give you the name and a potential description of an event at a music venue. Can you tell me the name of the artists playing at the event?",
    },
    {
      role: "system",
      content: `The event name is  ${event_name}`,
    },
    {
      role: "system",
      content: "Here is the description of a music event",
    },
    {
      role: "system",
      content: `Does that event seem to be cancelled?`,
    },
    {
      role: "system",
      content: `Can you format the artists names as json using the following format?
      {
        artists: [
          artistName: """Insert artist name here""",
        ]
        isEventCancelled: """Insert whether or not the event is cancelled as a boolean"""
      }`,
    },
  ];

  const completionConfig: CreateCompletionRequest = {
    model: "gpt-3.5-turbo",
    messages,
    max_tokens: 256,
    temperature: 0,
    // stream: true,
  };
  const aiResponse = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(completionConfig),
  });
  const aiJson = await aiResponse.json();
  const { artists, isEventCancelled } = JSON.parse(
    aiJson.choices[0].message.content
  );
  const output = {
    eventName: event_name,
    artists,
    isEventCancelled,
  };
  const { data, error } = await supabaseClient
    .from("eventMetadata")
    .insert({
      event: id,
      artists,
      isEventCancelled,
      source: "OpenAIScrape",
    })
    .select();
  console.log("data", data);
  console.log("errror", error);
  const { data2, error2 } = await supabaseClient
    .from("events")
    .upsert({
      id,
      stage: "OpenAIScrapeComplete",
    })
    .select();
    console.log("data2", data2);
    console.log("errror2", error2);
  console.log(aiJson);
  return new Response(JSON.stringify(output), {
    headers: { "Content-Type": "application/json" },
  });
});
