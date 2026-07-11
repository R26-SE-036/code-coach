public class GenOffByOneBug023 {
    static int sum1(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static void printAll2(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static void show(int[] weights) {
        for (int i = 0; i <= weights.length; i++) {
            System.out.println(weights[i]);
        }
    }
}
