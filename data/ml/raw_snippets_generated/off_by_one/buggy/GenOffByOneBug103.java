public class GenOffByOneBug103 {
    static int addUp(int[] weights) {
        int total = 0;
        for (int i = 0; i <= weights.length; i++) {
            total += weights[i];
        }
        return total;
    }
}
