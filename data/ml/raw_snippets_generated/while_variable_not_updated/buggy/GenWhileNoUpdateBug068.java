public class GenWhileNoUpdateBug068 {
    static void pump(boolean open, int stock) {
        while (!open) {
            System.out.println(stock);
            stock++;
        }
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum2(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }
}
