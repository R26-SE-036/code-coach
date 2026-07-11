public class GenWhileNoUpdateFix050 {
    static void countdown(int limit) {
        while (limit > 0) {
            System.out.println("left: " + limit);
            limit--;
        }
    }

    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }
}
