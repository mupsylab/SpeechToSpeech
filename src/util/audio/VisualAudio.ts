interface GradientOption {
    offset: number;
    color: string
}
type Color = GradientOption[] | string | CanvasGradient | CanvasPattern;
interface Audio {
    currAudioArray: Uint8Array;
}
interface VisualAudioOption {
    width: number,
    height: number,
    baseRadius: number,
    barWidth: number,
    rotationAngle: number,

    fillStyle: Color,
    strokeStyle: Color,
    record: {
        barStrokeStyle: Color
    },
    player: {
        barStrokeStyle: Color
    }
}

export class VisualAudio {
    private dom: HTMLCanvasElement | null;
    private options: VisualAudioOption;

    private continue: boolean = false;
    constructor(opts?: Partial<VisualAudioOption>) {
        this.dom = null;
        this.options = {
            width: 400,
            height: 400,
            baseRadius: 100,
            barWidth: 4,
            rotationAngle: 0,

            fillStyle: window.getComputedStyle(document.documentElement).getPropertyValue("--dashboard-background"),
            strokeStyle: window.getComputedStyle(document.documentElement).getPropertyValue("--fc-suggest-bg"),
            record: {
                barStrokeStyle: [
                    { offset: 0, color: "#00ff87" },
                    { offset: 0.5, color: "#BF8E69" },
                    { offset: 1, color: "#00ff87" },
                ]
            },
            player: {
                barStrokeStyle: [
                    { offset: 0, color: "#00ff87" },
                    { offset: 0.5, color: "#60efff" },
                    { offset: 1, color: "#00ff87" },
                ]
            },
            ...opts
        }
    }
    private getGradientStyle(colors: Color) {
        if (!this.dom) return "";
        const ctx = this.dom.getContext("2d");
        if (!ctx) return "";
        // 创建渐变
        const { width, height } = this.dom;
        if (colors instanceof Array) {
            const gradient = ctx.createLinearGradient(0, 0, width, height);
            colors.forEach(item => {
                gradient.addColorStop(item.offset, item.color);
            });
            return gradient;
        } else {
            return colors;
        }
    }
    private drawBar(ctx: CanvasRenderingContext2D,
        centerX: number, centerY: number,
        angle: number, radius: number,
        barHeight: number, width: number,
        barStrokeStyle: Color
    ) {
        const startX = centerX + Math.cos(angle) * radius;
        const startY = centerY + Math.sin(angle) * radius;
        const endX = centerX + Math.cos(angle) * (radius + barHeight);
        const endY = centerY + Math.sin(angle) * (radius + barHeight);

        ctx.beginPath();
        ctx.lineWidth = width;
        ctx.strokeStyle = this.getGradientStyle(barStrokeStyle);
        ctx.lineCap = 'round';
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.stroke();
    }
    private draw(record: Uint8Array, player: Uint8Array) {
        if (!this.dom) return 0;
        const ctx = this.dom.getContext("2d");
        if (!ctx) return 0;

        const { width, height } = this.dom;
        const centerX = width / 2;
        const centerY = height / 2;

        // 清除画布
        ctx.fillStyle = this.getGradientStyle(this.options.fillStyle);
        ctx.fillRect(0, 0, width, height);

        // 绘制中心圆
        ctx.beginPath();
        ctx.arc(centerX, centerY, this.options.baseRadius as number - 20, 0, Math.PI * 2);
        ctx.strokeStyle = this.getGradientStyle(this.options.strokeStyle);
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.globalAlpha = 0.5;

        // 绘制频谱柱状图
        const recordBarCount = record.length; // 使用一半的数据点以获得更好的视觉效果
        const recordAngleStep = (Math.PI * 2) / recordBarCount;
        for (let i = 0; i < recordBarCount; i++) {
            const value = record[i];
            const barHeight = (value / 255) * 100; // 最大高度100像素
            const angle = i * recordAngleStep + (this.options.rotationAngle as number);

            this.drawBar(
                ctx,
                centerX,
                centerY,
                angle,
                this.options.baseRadius as number,
                barHeight,
                this.options.barWidth as number,
                this.options.record.barStrokeStyle
            );
        }

        const playerBarCount = player.length; // 使用一半的数据点以获得更好的视觉效果
        const playerAngleStep = (Math.PI * 2) / playerBarCount;
        for (let i = 0; i < playerBarCount; i++) {
            const value = player[i];
            const barHeight = (value / 255) * 100; // 最大高度100像素
            const angle = i * playerAngleStep + (this.options.rotationAngle as number);

            this.drawBar(
                ctx,
                centerX,
                centerY,
                angle,
                this.options.baseRadius as number,
                barHeight,
                this.options.barWidth as number,
                this.options.player.barStrokeStyle
            );
        }
        (this.options.rotationAngle as number) += 0.001;
    }
    public start(id: string, record: Audio, player: Audio) {
        if (this.continue) return 0;
        this.continue = true;

        this.dom = document.querySelector(id);
        if (!this.dom) return;
        this.dom.width = this.options.width;
        this.dom.height = this.options.height;

        const dd = () => {
            if (this.continue) window.requestAnimationFrame(dd)
            this.draw(record.currAudioArray, player.currAudioArray);
        }
        dd();
    }
    public stop() {
        this.continue = false;
    }
}