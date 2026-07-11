public class GenOffByOneBug040 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void show(int[] weights) {
        for (int i = 0; i <= weights.length; i++) {
            System.out.println(weights[i]);
        }
    }
}
