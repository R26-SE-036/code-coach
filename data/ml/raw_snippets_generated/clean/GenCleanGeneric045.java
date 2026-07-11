public class GenCleanGeneric045 {
    static void printAll1(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static int sum2(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
