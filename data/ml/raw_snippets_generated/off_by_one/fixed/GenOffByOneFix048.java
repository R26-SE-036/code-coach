public class GenOffByOneFix048 {
    static void show(int[] ages) {
        for (int i = 0; i < ages.length; i++) {
            System.out.println(ages[i]);
        }
    }

    static String describe1(int level) {
        if (level < 10) {
            return "low";
        } else if (level > 50) {
            return "high";
        }
        return "medium";
    }
}
