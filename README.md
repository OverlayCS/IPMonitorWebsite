```mermaid
flowchart LR
    You -->|channel.Send| P((Packet))
    P -->|OnMessage| B[Player B]
    P -->|OnMessage| C[Player C]
```
