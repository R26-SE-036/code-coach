public class GenWhileNoUpdateFix159 {
    static int drain1(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void countdown(int points) {
        while (points > 0) {
            System.out.println("left: " + points);
            points--;
        }
    }
}
