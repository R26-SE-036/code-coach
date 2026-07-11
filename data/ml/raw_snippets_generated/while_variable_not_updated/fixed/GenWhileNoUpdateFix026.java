public class GenWhileNoUpdateFix026 {
    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static boolean isEven2(int quota) {
        return quota % 2 == 0;
    }

    static int gather(int level, int stock) {
        int sum = 0;
        while (level < stock) {
            sum += level;
            level++;
        }
        return sum;
    }
}
