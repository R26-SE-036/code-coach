public class GenOffByOneBug139 {
    static void show(int[] ratings) {
        for (int i = 0; i <= ratings.length; i++) {
            System.out.println(ratings[i]);
        }
    }
}
