type EventCallback = (...args: any[]) => void;

export class EventManager<EventType extends string | number | symbol> {
  private events: Map<EventType, EventCallback[]>;

  constructor() {
    this.events = new Map();
  }

  // 注册事件
  addEventListener(event: EventType, callback: EventCallback): void {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }
    this.events.get(event)?.push(callback);
  }

  // 移除事件
  removeEventListener(event: EventType, callback: EventCallback): void {
    const listeners = this.events.get(event);
    if (listeners) {
      this.events.set(event, listeners.filter(cb => cb !== callback));
    }
  }

  // 触发事件
  dispatchEvent(event: EventType, ...args: any[]): void {
    const listeners = this.events.get(event);
    if (listeners) {
      listeners.forEach(callback => callback(...args));
    }
  }
}
