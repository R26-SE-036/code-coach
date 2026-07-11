public class GenOffByOneBug008 {
    static void show(int[] scores) {
        for (int i = 0; i <= scores.length; i++) {
            System.out.println(scores[i]);
        }
    }
}
