public class OffByOneLoopBoundary3 {
    public static double sumTemperatures(double[] readings) {
        double total = 0;
        for (int i = 0; i <= readings.length; i++) {
            total += readings[i];
        }
        return total;
    }

    public static void main(String[] args) {
        double[] temps = { 36.6, 37.1, 38.0, 36.9 };
        System.out.println("Total: " + sumTemperatures(temps));
    }
}
