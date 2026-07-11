public class GenIncorrectConditionalFix131 {
    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static String report(boolean done) {
        if (done == true) {
            return "draft";
        }
        return "active";
    }

    static void printAll2(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }
}
