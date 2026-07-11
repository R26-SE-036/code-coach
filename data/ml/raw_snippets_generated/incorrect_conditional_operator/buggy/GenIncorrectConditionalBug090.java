public class GenIncorrectConditionalBug090 {
    static String report(boolean done) {
        if (done = true) {
            return "closed";
        }
        return "draft";
    }

    static int sum1(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static void printAll2(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static void printAll3(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }
}
