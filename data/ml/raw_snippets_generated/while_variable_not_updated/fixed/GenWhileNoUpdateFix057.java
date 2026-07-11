public class GenWhileNoUpdateFix057 {
    static int sum1(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static void pump(boolean done, int stock) {
        while (!done) {
            System.out.println(stock);
            stock++;
            done = stock > 10;
        }
    }
}
