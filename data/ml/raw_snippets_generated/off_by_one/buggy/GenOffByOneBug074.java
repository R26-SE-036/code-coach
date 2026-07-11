public class GenOffByOneBug074 {
    static void show(int[] scores) {
        for (int i = 0; i <= scores.length; i++) {
            System.out.println(scores[i]);
        }
    }

    static int sum1(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
