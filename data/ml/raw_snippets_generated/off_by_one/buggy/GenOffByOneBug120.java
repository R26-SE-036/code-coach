public class GenOffByOneBug120 {
    static String describe1(int points) {
        if (points < 10) {
            return "low";
        } else if (points > 50) {
            return "high";
        }
        return "medium";
    }

    static void show(int[] sizes) {
        for (int i = 0; i <= sizes.length; i++) {
            System.out.println(sizes[i]);
        }
    }
}
