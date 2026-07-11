public class GenOffByOneFix078 {
    static void show(int[] weights) {
        for (int i = 0; i < weights.length; i++) {
            System.out.println(weights[i]);
        }
    }

    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static int sum2(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }
}
