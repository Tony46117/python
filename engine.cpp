#include <vector>
#include <cmath>
#include <random>
#include <algorithm>
#include <cstring>

struct Particle {
    float x, y;
    float vx, vy;
    float life, max_life;
    float r, g, b;
    float size;
};

struct GameData {
    int grid_w, grid_h;
    std::vector<std::pair<int,int>> snake;
    std::pair<int,int> food;
    int direction;
    int score;
    bool game_over;
    std::mt19937 rng;
    std::vector<Particle> particles;
    std::vector<std::pair<float,float>> trail;
};

static GameData* g = nullptr;

extern "C" {

void engine_init(int grid_w, int grid_h) {
    if (g) delete g;
    g = new GameData();
    g->grid_w = grid_w;
    g->grid_h = grid_h;
    g->direction = 1;
    g->score = 0;
    g->game_over = false;
    g->rng.seed(std::random_device{}());
}

void engine_free() {
    if (g) { delete g; g = nullptr; }
}

static void spawn_food() {
    std::vector<std::pair<int,int>> free_cells;
    for (int x = 0; x < g->grid_w; x++) {
        for (int y = 0; y < g->grid_h; y++) {
            bool occupied = false;
            for (auto& s : g->snake) {
                if (s.first == x && s.second == y) { occupied = true; break; }
            }
            if (!occupied) free_cells.push_back({x, y});
        }
    }
    if (!free_cells.empty()) {
        std::uniform_int_distribution<int> dist(0, (int)free_cells.size() - 1);
        g->food = free_cells[dist(g->rng)];
    }
}

void engine_reset() {
    int cx = g->grid_w / 2;
    int cy = g->grid_h / 2;
    g->snake.clear();
    g->snake.push_back({cx, cy});
    g->snake.push_back({cx - 1, cy});
    g->snake.push_back({cx - 2, cy});
    g->direction = 1;
    g->score = 0;
    g->game_over = false;
    g->particles.clear();
    g->trail.clear();
    spawn_food();
}

void engine_set_direction(int d) {
    if (!g || g->game_over) return;
    if (std::abs(d - g->direction) == 2) return;
    if (d < 0 || d > 3) return;
    g->direction = d;
}

static void spawn_eat_particles(int gx, int gy) {
    std::uniform_real_distribution<float> dist(-0.15f, 0.15f);
    std::uniform_real_distribution<float> spd(0.02f, 0.08f);
    for (int i = 0; i < 15; i++) {
        float angle = (float)i / 15.0f * 6.28318f;
        Particle p;
        p.x = gx + 0.5f;
        p.y = gy + 0.5f;
        p.vx = std::cos(angle) * spd(g->rng) + dist(g->rng);
        p.vy = std::sin(angle) * spd(g->rng) + dist(g->rng);
        p.life = 1.0f;
        p.max_life = 1.0f;
        p.r = 0.2f + (float)(i % 3) * 0.3f;
        p.g = 0.8f + (float)(i % 2) * 0.2f;
        p.b = 0.1f;
        p.size = 3.0f + (float)(i % 4);
        g->particles.push_back(p);
    }
}

static void spawn_death_particles() {
    for (auto& seg : g->snake) {
        for (int i = 0; i < 5; i++) {
            std::uniform_real_distribution<float> dist(-0.1f, 0.1f);
            Particle p;
            p.x = seg.first + 0.5f;
            p.y = seg.second + 0.5f;
            p.vx = dist(g->rng);
            p.vy = dist(g->rng);
            p.life = 1.0f;
            p.max_life = 1.0f;
            p.r = 0.9f;
            p.g = 0.2f;
            p.b = 0.1f;
            p.size = 4.0f;
            g->particles.push_back(p);
        }
    }
}

int engine_step() {
    if (!g || g->game_over) return 0;

    auto head = g->snake[0];
    int nx = head.first, ny = head.second;

    switch (g->direction) {
        case 0: ny--; break;
        case 1: nx++; break;
        case 2: ny++; break;
        case 3: nx--; break;
    }

    if (nx < 0 || nx >= g->grid_w || ny < 0 || ny >= g->grid_h) {
        g->game_over = true;
        spawn_death_particles();
        return 0;
    }

    for (auto& s : g->snake) {
        if (s.first == nx && s.second == ny) {
            g->game_over = true;
            spawn_death_particles();
            return 0;
        }
    }

    g->snake.insert(g->snake.begin(), {nx, ny});

    if (nx == g->food.first && ny == g->food.second) {
        g->score += 10;
        spawn_eat_particles(g->food.first, g->food.second);
        spawn_food();
    } else {
        g->snake.pop_back();
    }

    if (!g->snake.empty()) {
        g->trail.push_back({(float)g->snake[0].first + 0.5f, (float)g->snake[0].second + 0.5f});
        if ((int)g->trail.size() > 20) g->trail.erase(g->trail.begin());
    }

    return 1;
}

void engine_update_particles() {
    if (!g) return;
    for (auto it = g->particles.begin(); it != g->particles.end(); ) {
        it->x += it->vx;
        it->y += it->vy;
        it->vy += 0.002f;
        it->life -= 0.025f;
        if (it->life <= 0.0f) {
            it = g->particles.erase(it);
        } else {
            ++it;
        }
    }
}

// Returns packed data: [snake_x0, snake_y0, snake_x1, snake_y1, ..., -1, food_x, food_y, score, game_over, direction,
//                       num_particles, (px, py, life, r, g, b, size)*num_particles,
//                       num_trail, (tx, ty)*num_trail]
int engine_get_state(float* out_snake, int* out_snake_len,
                     float* out_food, int* out_score, int* out_game_over, int* out_direction,
                     float* out_particles, int* out_particle_count,
                     float* out_trail, int* out_trail_len) {
    if (!g) return -1;

    *out_snake_len = (int)g->snake.size();
    for (int i = 0; i < (int)g->snake.size(); i++) {
        out_snake[i * 2] = (float)g->snake[i].first;
        out_snake[i * 2 + 1] = (float)g->snake[i].second;
    }

    out_food[0] = (float)g->food.first;
    out_food[1] = (float)g->food.second;

    *out_score = g->score;
    *out_game_over = g->game_over ? 1 : 0;
    *out_direction = g->direction;

    *out_particle_count = (int)g->particles.size();
    for (int i = 0; i < (int)g->particles.size(); i++) {
        int off = i * 7;
        out_particles[off + 0] = g->particles[i].x;
        out_particles[off + 1] = g->particles[i].y;
        out_particles[off + 2] = g->particles[i].life / g->particles[i].max_life;
        out_particles[off + 3] = g->particles[i].r;
        out_particles[off + 4] = g->particles[i].g;
        out_particles[off + 5] = g->particles[i].b;
        out_particles[off + 6] = g->particles[i].size;
    }

    *out_trail_len = (int)g->trail.size();
    for (int i = 0; i < (int)g->trail.size(); i++) {
        out_trail[i * 2] = g->trail[i].first;
        out_trail[i * 2 + 1] = g->trail[i].second;
    }

    return 0;
}

} // extern "C"
